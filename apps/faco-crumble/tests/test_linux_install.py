"""Real installer / launcher tests against disposable Linux/XDG home directories."""
import json
import os
import re
import select
import signal
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def temp_env(home: Path):
    env = dict(os.environ)
    for key in ('XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME',
                'FACO_INSTALL_PREFIX', 'FACO_VENV_PATH', 'FACO_SHARED_ROOT'):
        env.pop(key, None)
    env.update(HOME=str(home), FACO_NO_GUI='1', FACO_ALLOW_ROOT_INSTALL='1')
    return env


def check(*flags, env):
    return subprocess.run(['./install.sh', '--no-launch', '--noninteractive', *flags],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, timeout=30)


class LinuxInstallTest(unittest.TestCase):
    def test_fresh_user_default_xdg_install_and_launcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'fresh-linux-user'
            home.mkdir()
            env = temp_env(home)
            result = check(env=env)
            self.assertEqual(result.returncode, 0, result.stdout)
            app = home / '.local/share/faco-crumble/app'
            wrapper = home / '.local/bin/faco-crumble'
            desktop = home / '.local/share/applications/faco-crumble.desktop'
            self.assertTrue((app / 'public' / 'app.js').is_file())
            self.assertTrue(wrapper.is_file())
            self.assertTrue(os.access(wrapper, os.X_OK))
            self.assertIn(str(app / 'public/favicon.svg'), desktop.read_text())
            self.assertFalse((app / '_logs').exists())
            self.assertFalse((app / 'venv').exists())
            self.assertTrue((home / '.config/faco-crumble').is_dir())
            self.assertTrue((home / '.local/state/faco-crumble').is_dir())
            self.assertTrue((home / '.cache/faco-crumble').is_dir())
            # Run the actual installed wrapper, not the source-tree launcher.
            with socket.socket() as a, socket.socket() as b:
                a.bind(('127.0.0.1', 0)); b.bind(('127.0.0.1', 0))
                public_port, admin_port = a.getsockname()[1], b.getsockname()[1]
            child = subprocess.Popen([str(wrapper), '--local', '--no-open'], env={**env,
                'FACO_PORT':str(public_port), 'FACO_ADMIN_PORT':str(admin_port)},
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                deadline=time.monotonic()+15
                out=b''
                while time.monotonic()<deadline:
                    if child.poll() is not None:
                        self.fail('Installed application exited: ' + out.decode(errors='replace'))
                    r, _, _=select.select([child.stdout], [], [], .25)
                    if r: out += os.read(child.stdout.fileno(), 32768)
                    try:
                        with urllib.request.urlopen(f'http://127.0.0.1:{public_port}/healthz', timeout=.25) as response:
                            if json.load(response)['ok']:
                                break
                    except (OSError, ValueError):
                        pass
                else:
                    self.fail('Installed service did not become healthy: ' + out.decode(errors='replace'))
                deadline=time.monotonic()+2
                while b'LOCAL CONTROL CENTER' not in out and time.monotonic()<deadline:
                    r, _, _=select.select([child.stdout], [], [], .25)
                    if r: out += os.read(child.stdout.fileno(), 32768)
                self.assertIn(b'LOCAL CONTROL CENTER', out)
            finally:
                child.terminate()
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=5)
                child.stdout.close()

    def test_custom_drive_unavailable_aborts_without_creating_fake_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'home'; home.mkdir()
            missing = Path(tmp) / 'unmounted' / 'external_drive' / 'faco-crumble'
            env = temp_env(home)
            result = check('--prefix', str(missing), env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Use OS Default Location', result.stdout)
            self.assertIn('Cancel Installation', result.stdout)
            self.assertFalse(missing.exists())
            self.assertFalse((home / '.local/share/faco-crumble/app').exists())

    def test_explicit_custom_location_with_spaces_and_xdg_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / 'ubuntu-user'; home.mkdir()
            preferred = base / 'my mounted disk'; preferred.mkdir()
            destination = preferred / 'Crumble App'
            env = temp_env(home)
            env['XDG_DATA_HOME'] = str(base / 'user-data')
            env['XDG_CONFIG_HOME'] = str(base / 'user-config')
            env['XDG_STATE_HOME'] = str(base / 'user-state')
            env['XDG_CACHE_HOME'] = str(base / 'user-cache')
            result = check('--prefix', str(destination), env=env)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue((destination/'run.sh').is_file())
            self.assertFalse((base/'user-data/faco-crumble/app').exists())
            self.assertTrue((base/'user-config/faco-crumble').is_dir())
            self.assertTrue((base/'user-state/faco-crumble').is_dir())
            self.assertTrue((base/'user-cache/faco-crumble').is_dir())
            self.assertIn(str(destination/'run.sh'), (home/'.local/bin/faco-crumble').read_text())
            self.assertFalse(any('owner/Faco' in str(p) for p in destination.rglob('*')))
            # Reinstall over the same destination to verify upgrade does not recursively copy itself.
            again = check('--prefix', str(destination), env=env)
            self.assertEqual(again.returncode, 0, again.stdout)
            self.assertTrue((destination/'public/app.js').is_file())

if __name__ == '__main__': unittest.main()
