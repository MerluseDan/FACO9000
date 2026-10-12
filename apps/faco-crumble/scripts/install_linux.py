#!/usr/bin/env python3
"""FACO Crumble XDG-aware, user-scope Linux installer; no sudo or private mount needed."""
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import stat
import sys
import tempfile
from pathlib import Path

APP = 'faco-crumble'
ROOT = Path(__file__).resolve().parents[1]
FILES = ('README.md', 'RELEASE_NOTES.md', 'RELEASE_MANIFEST.json', 'Caddyfile.example',
         'requirements.txt', 'server.py', 'launcher.py', 'run.sh', 'start.sh', 'install.sh', '.gitignore')
DIRS = ('assets', 'public', 'admin', 'scripts', 'tests')
EXECUTABLES = ('run.sh', 'start.sh', 'install.sh', 'launcher.py', 'scripts/doctor.py',
               'scripts/install_linux.py')


def xdg_path(variable: str, suffix: str) -> Path:
    value = os.environ.get(variable, '').strip()
    if value and Path(value).is_absolute():
        return Path(value).expanduser()
    return Path.home() / suffix


def paths():
    data = xdg_path('XDG_DATA_HOME', '.local/share')
    return {
        'default_app': data / APP / 'app',
        'venv': data / APP / 'venv',
        'config': xdg_path('XDG_CONFIG_HOME', '.config') / APP,
        'state': xdg_path('XDG_STATE_HOME', '.local/state') / APP,
        'cache': xdg_path('XDG_CACHE_HOME', '.cache') / APP,
        'bin': Path.home() / '.local' / 'bin',
        'desktop': data / 'applications',
    }


def writable_parent(path: Path) -> bool:
    """Custom location MUST already have a writable parent; do not fabricate missing mounts."""
    parent = path.parent
    return (parent.is_dir() and os.access(parent, os.W_OK | os.X_OK)
            and not parent.is_symlink() and not path.is_symlink())


def destination(args, default: Path) -> Path:
    preferred = args.prefix or os.environ.get('FACO_INSTALL_PREFIX', '').strip()
    if not preferred:
        return default
    candidate = Path(preferred).expanduser().absolute()
    if candidate == default:
        return default
    valid = writable_parent(candidate)
    if valid:
        return candidate
    print('\nCUSTOM INSTALL LOCATION IS UNAVAILABLE:', candidate, file=sys.stderr)
    print('Its parent directory is missing, not writable, or is a symlink.', file=sys.stderr)
    print('This can mean a preferred external drive is not mounted.', file=sys.stderr)
    print('  [1] Use OS Default Location:', default, file=sys.stderr)
    print('  [2] Cancel Installation', file=sys.stderr)
    if args.noninteractive or not sys.stdin.isatty():
        raise RuntimeError('No implicit fallback. Re-run without --prefix for the OS default, or mount your drive.')
    print('Choose 1 or 2: ', end='', file=sys.stderr, flush=True)
    answer = sys.stdin.readline().strip()
    if answer == '1':
        return default
    raise RuntimeError('Installation cancelled; no files installed.')


def assert_safe_destination(src: Path, dest: Path) -> None:
    path = dest.resolve(strict=False)
    forbidden = {Path('/'), Path.home().resolve(), Path('/opt'), Path('/usr'),
                 Path('/usr/local'), src.resolve(), src.parent.resolve()}
    if path in forbidden or path == src.resolve() or src.resolve().is_relative_to(path):
        raise RuntimeError(f'Unsafe installation destination: {path}')
    if path.is_symlink():
        raise RuntimeError('Installation destination must not be a symlink.')
    if len(path.parts) < 3:
        raise RuntimeError('Install to an application directory, not a filesystem root.')


def stage_application(src: Path, staging: Path) -> None:
    for file in FILES:
        source = src / file
        if not source.is_file() or source.is_symlink():
            raise RuntimeError(f'Missing or unsafe source file: {file}')
        shutil.copy2(source, staging / file)
    for name in DIRS:
        source = src / name
        if not source.is_dir() or source.is_symlink():
            raise RuntimeError(f'Missing or unsafe source directory: {name}')
        shutil.copytree(source, staging / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc',
                                              '_logs', '.pytest_cache', '_qa_*'))
    for file in EXECUTABLES:
        candidate = staging / file
        candidate.chmod(candidate.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_atomic(target: Path, contents: str, mode: int) -> None:
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.faco-write-', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(contents)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(name, mode)
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def install(args) -> Path:
    if sys.platform != 'linux':
        raise RuntimeError('This installer is for Linux; macOS/Windows require separate installers.')
    if os.geteuid() == 0 and os.environ.get('FACO_ALLOW_ROOT_INSTALL') != '1':
        raise RuntimeError('Do not run as root. Use a normal Linux account; this is a per-user install.')
    locations = paths()
    target = destination(args, locations['default_app'])
    assert_safe_destination(ROOT, target)
    if target == locations['default_app']:
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not writable_parent(target):
        raise RuntimeError(f'Cannot write to installation parent: {target.parent}')
    target_parent = target.parent
    staging = Path(tempfile.mkdtemp(prefix='.faco-install-', dir=target_parent))
    backup = None
    try:
        stage_application(ROOT, staging)
        if target.exists():
            if not target.is_dir():
                raise RuntimeError('Existing install is not a directory.')
            backup = Path(tempfile.mkdtemp(prefix='.faco-backup-', dir=target_parent))
            backup.rmdir()
            target.rename(backup)
        try:
            staging.rename(target)
        except Exception:
            if backup and backup.exists():
                backup.rename(target)
            raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    if backup and backup.exists():
        shutil.rmtree(backup)
    # Linux/XDG state paths. Never create custom drive locations implicitly.
    for category in ('config', 'state', 'cache'):
        locations[category].mkdir(mode=0o700, parents=True, exist_ok=True)
    wrapper = locations['bin'] / APP
    wrapper_content = '#!/usr/bin/env bash\nset -Eeuo pipefail\nexec ' + shlex.quote(str(target / 'run.sh')) + ' "$@"\n'
    write_atomic(wrapper, wrapper_content, 0o755)
    desktop = locations['desktop'] / (APP + '.desktop')
    # The FreeDesktop Exec syntax requires quoting when spaces occur. No shell evaluation.
    desktop_exec = '"' + str(wrapper).replace('\\', '\\\\').replace('"', '\\"') + '"'
    desktop_icon = '"' + str(target / 'public/favicon.svg').replace('\\', '\\\\').replace('"', '\\"') + '"'
    write_atomic(desktop, '\n'.join([
        '[Desktop Entry]', 'Type=Application', 'Version=1.0',
        'Name=FACO Crumble', 'Comment=Private invite-only browser calling and messaging',
        'Exec=' + desktop_exec + ' --quick', 'Icon=' + desktop_icon,
        'Terminal=true', 'Categories=Network;AudioVideo;', 'StartupNotify=false', ''
    ]), 0o644)
    print('\nFACO CRUMBLE v0.5.1 INSTALLED')
    for label, path in [('Application', target), ('Command', wrapper), ('Desktop shortcut', desktop),
                        ('Settings', locations['config']), ('Runtime environment', locations['venv']),
                        ('Logs', locations['state']), ('Cache', locations['cache'])]:
        print(f'  {label}: {path}')
    print('Use:', wrapper, '--quick')
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefix', help='Optional existing custom parent + app folder; standard XDG location is default')
    parser.add_argument('--noninteractive', action='store_true')
    args = parser.parse_args()
    try:
        target = install(args)
        print('FACO_INSTALLED_PATH=' + str(target), flush=True)
    except (OSError, RuntimeError) as exc:
        print('FACO INSTALL ERROR:', exc, file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
