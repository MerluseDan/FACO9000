#!/usr/bin/env python3
"""Start isolated public WebRTC signaling + localhost-only graphical QR console.

Quick Tunnel restarts automatically. Reissue invites when connector exits, URL changes,
or a logged tunnel connection drops and subsequently reconnects.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import shutil
import subprocess
import sys
import platform
import webbrowser
from pathlib import Path
from aiohttp import web

from server import ControlState, create_admin_app, create_app, valid_base_url, load_guest_settings

ROOT = Path(__file__).resolve().parent
TUNNEL_URL = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', re.IGNORECASE)


def settings_home() -> Path:
    if os.getenv('FACO_CONFIG_DIR'):
        return Path(os.environ['FACO_CONFIG_DIR']).expanduser()
    if sys.platform == 'win32':
        return Path(os.getenv('APPDATA') or (Path.home() / 'AppData' / 'Roaming')) / 'FACO' / 'Crumble'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'FACO' / 'Crumble'
    return Path(os.getenv('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'faco-crumble'


def log_home() -> Path:
    if os.getenv('FACO_STATE_DIR'):
        return Path(os.environ['FACO_STATE_DIR']).expanduser()
    if sys.platform == 'win32':
        return Path(os.getenv('LOCALAPPDATA') or (Path.home() / 'AppData' / 'Local')) / 'FACO' / 'Crumble' / 'Logs'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Logs' / 'FACO' / 'Crumble'
    return Path(os.getenv('XDG_STATE_HOME', str(Path.home() / '.local' / 'state'))) / 'faco-crumble'


def cloudflared_path() -> str | None:
    override = os.environ.get('FACO_CLOUDFLARED', '').strip()
    found = shutil.which('cloudflared')
    candidates = [override, found]
    if sys.platform == 'win32':
        p = os.getenv('PROGRAMFILES') or r'C:\Program Files'
        candidates += [str(Path(p)/'cloudflared'/'cloudflared.exe'), str(Path.home()/'scoop'/'shims'/'cloudflared.exe')]
    elif sys.platform == 'darwin':
        candidates += ['/opt/homebrew/bin/cloudflared', '/usr/local/bin/cloudflared']
    else:
        candidates += [str(Path.home()/'.local'/'bin'/'cloudflared')]
    for path in candidates:
        if path and Path(path).is_file() and os.access(path, os.X_OK):
            return str(path)
    return None


def auto_open(url: str) -> bool:
    if os.environ.get('FACO_NO_GUI'):
        return False
    if sys.platform in ('win32','darwin'):
        try:
            return bool(webbrowser.open(url))
        except Exception:
            return False
    if not (os.getenv('DISPLAY') or os.getenv('WAYLAND_DISPLAY')):
        return False
    browser = shutil.which('xdg-open')
    if not browser:
        return False
    try:
        subprocess.Popen([browser, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        return True
    except OSError:
        return False


async def run_quick_tunnel(state: ControlState, binary: str, public_port: int):
    """No admin port is ever passed to cloudflared. Reconnects rotate invitations."""
    retry_seconds = 1
    logpath = log_home() / 'tunnel.log'
    logpath.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    while True:
        print('Starting Cloudflare HTTPS tunnel...', flush=True)
        state.tunnel_state = 'Connecting'
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                binary, 'tunnel', '--no-autoupdate', '--url', f'http://127.0.0.1:{public_port}',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            seen_url = ''
            lost_connection = False
            with logpath.open('a', encoding='utf8') as logfile:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    value = line.decode('utf8', errors='replace').strip()
                    logfile.write(value + '\n')
                    logfile.flush()
                    found = TUNNEL_URL.search(value)
                    if found:
                        url = found.group(0).rstrip('/')
                        if url != seen_url:
                            seen_url = url
                            previous = state.base_url
                            await state.set_tunnel(url)
                            if previous != url:
                                print(f'Public HTTPS link: {url}', flush=True)
                                print('The desktop control panel contains fresh public and private QR codes.', flush=True)
                            retry_seconds = 1
                    lower = value.lower()
                    if any(needle in lower for needle in ('connection terminated', 'unregistered tunnel connection',
                                                            'retrying connection', 'connection dropped')):
                        lost_connection = True
                        state.tunnel_state = 'Reconnecting'
                    if 'registered tunnel connection' in lower and 'unregistered tunnel connection' not in lower:
                        if lost_connection:
                            lost_connection = False
                            if state.base_url:
                                await state.rotate('Cloudflare connector re-established; invites expired')
                                print('Cloudflare reconnection: invitation QRs automatically refreshed.', flush=True)
                        if state.base_url:
                            state.tunnel_state = 'Active'
            await process.wait()
            print(f'Cloudflare process exited ({process.returncode}). Attempting reconnection.', flush=True)
        except asyncio.CancelledError:
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=4)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            raise
        except OSError as exc:
            print('Cloudflare could not start:', exc, flush=True)
        finally:
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=4)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
        # A new subprocess (even same public address) receives entirely new session credentials.
        state.base_url = ''
        state.tunnel_state = 'Reconnecting'
        await state.rotate('Cloudflare tunnel process stopped; invitations expired')
        await asyncio.sleep(retry_seconds)
        retry_seconds = min(retry_seconds * 2, 15)


async def run_services(args):
    if args.mode == 'domain' and not valid_base_url(args.domain):
        raise RuntimeError('Provide a valid https://hostname with no path, query or credentials.')
    if args.public_port == args.admin_port:
        raise RuntimeError('Public and private admin ports must be different.')
    binary = cloudflared_path() if args.mode == 'quick' else None
    if args.mode == 'quick' and not binary:
        raise RuntimeError('cloudflared is missing. Install it first, or choose --local / --domain.')
    base = (f'http://localhost:{args.public_port}' if args.mode == 'local'
            else args.domain.rstrip('/') if args.mode == 'domain' else '')
    settings_path = settings_home() / 'settings.json'
    # Preserve the last participant count when upgrading from the old FACO Private Talk launcher.
    legacy_settings = (Path(os.getenv('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'faco-private-talk' / 'settings.json')
    count_source = settings_path if settings_path.exists() else legacy_settings
    state = ControlState(count=load_guest_settings(count_source), base_url=base, settings_path=settings_path)
    pub_runner = web.AppRunner(create_app(state), access_log=None)
    adm_runner = web.AppRunner(create_admin_app(state, args.admin_port), access_log=None)
    started_pub = started_adm = False
    tunnel_task = None
    try:
        await pub_runner.setup()
        await web.TCPSite(pub_runner, '127.0.0.1', args.public_port).start()
        started_pub = True
        await adm_runner.setup()
        await web.TCPSite(adm_runner, '127.0.0.1', args.admin_port).start()
        started_adm = True
        url = f'http://127.0.0.1:{args.admin_port}/#admin={state.admin_token}'
        print('\n' + '=' * 62, flush=True)
        print('FACO CRUMBLE  |  Desktop Invite & QR Control Center', flush=True)
        print('=' * 62, flush=True)
        print('LOCAL CONTROL CENTER (never share):', url, sep='\n', flush=True)
        print('PUBLIC CALL SERVICE: 127.0.0.1:' + str(args.public_port), flush=True)
        print('ADMIN CONTROLS:      127.0.0.1:' + str(args.admin_port), flush=True)
        print('Every app start creates new participant QR credentials.', flush=True)
        if args.mode == 'domain':
            print('External domains: use the Rotate All button after restarting your external proxy.', flush=True)
        if not args.no_open:
            if auto_open(url):
                print('Opened your local control panel in the default browser.', flush=True)
            else:
                print('Desktop browser could not open automatically. Open the local control URL above.', flush=True)
        if args.mode == 'quick':
            tunnel_task = asyncio.create_task(run_quick_tunnel(state, binary, args.public_port))
            await tunnel_task
        else:
            print('Call service running; press Ctrl+C to stop.', flush=True)
            await asyncio.Event().wait()
    finally:
        if tunnel_task:
            tunnel_task.cancel()
            try:
                await tunnel_task
            except asyncio.CancelledError:
                pass
        if started_adm:
            await adm_runner.cleanup()
        if started_pub:
            await pub_runner.cleanup()


def main():
    parser = argparse.ArgumentParser(description='FACO Crumble private browser calling + localhost QR dashboard')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--quick', dest='mode', action='store_const', const='quick', help='Temporary Cloudflare URL (default)')
    group.add_argument('--local', dest='mode', action='store_const', const='local', help='Local-only test; remote mic needs HTTPS')
    group.add_argument('--domain', help='Your existing HTTPS public domain (reverse proxy not created)')
    parser.set_defaults(mode='quick')
    parser.add_argument('--no-open', action='store_true', help='Do not launch the desktop control panel in a browser')
    parser.add_argument('--public-port', type=int, default=int(os.getenv('FACO_PORT', '8787')))
    parser.add_argument('--admin-port', type=int, default=int(os.getenv('FACO_ADMIN_PORT', '8788')))
    args = parser.parse_args()
    if args.domain:
        args.mode = 'domain'
    if args.public_port < 1024 or args.public_port > 65535 or args.admin_port < 1024 or args.admin_port > 65535:
        parser.error('Ports must be between 1024 and 65535')
    try:
        asyncio.run(run_services(args))
    except KeyboardInterrupt:
        print('\nFACO Crumble stopped. All active invitations are expired.', flush=True)
    except (RuntimeError, OSError) as exc:
        print('ERROR:', exc, file=sys.stderr, flush=True)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
