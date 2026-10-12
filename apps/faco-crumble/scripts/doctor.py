#!/usr/bin/env python3
"""Fast non-destructive startup Doctor; standard test suite available separately."""
from pathlib import Path
from importlib.util import find_spec
import os
import shutil
import socket
import sys

root = Path(__file__).resolve().parents[1]
required = ('server.py','launcher.py','admin/index.html','admin/admin.js','admin/admin.css',
            'public/index.html','public/app.js','public/style.css','public/favicon.svg','requirements.txt')
errors=[]
for name in required:
    candidate=root / name
    if not candidate.is_file() or candidate.is_symlink(): errors.append('Missing/symlinked '+name)
for name in ('aiohttp','qrcode'):
    if not find_spec(name): errors.append('Missing Python module '+name)
for key, default in (('FACO_PORT','8787'),('FACO_ADMIN_PORT','8788')):
    try:
        port=int(os.getenv(key,default))
        if not 1024 <= port <= 65535: errors.append(key+' must be between 1024 and 65535')
    except ValueError: errors.append(key+' must be a number')
if os.getenv('FACO_PORT','8787') == os.getenv('FACO_ADMIN_PORT','8788'):
    errors.append('Public and private admin ports cannot match')
if errors:
    for issue in errors: print('FAILED startup Doctor:',issue,file=sys.stderr)
    raise SystemExit(1)
# Asset and user-facing call-shell contracts. Keep Doctor fast and read-only.
front = (root / 'public' / 'index.html').read_text(encoding='utf8')
style = (root / 'public' / 'style.css').read_text(encoding='utf8')
for element in ('callInfinityStage','optionsPanel','audioInputSelect','audioOutputSelect',
                'saveOptionsButton','resetOptionsButton','callDock'):
    if f'id="{element}"' not in front: errors.append('Missing user-facing option: '+element)
if 'infinityFlow' not in style or 'prefers-reduced-motion' not in style:
    errors.append('Missing lightweight call animation or reduced-motion rule')
if errors:
    for issue in errors: print('FAILED startup Doctor:', issue, file=sys.stderr)
    raise SystemExit(1)
print('PASSED startup Doctor: Python, runtime, ports, UI actions and lightweight infinity animation')
if not (os.getenv('DISPLAY') or os.getenv('WAYLAND_DISPLAY')):
    print('NOTE: No desktop display detected. Admin browser address will be printed.')
if not os.getenv('FACO_ICE_SERVERS_JSON'):
    print('NOTE: Public STUN only; restrictive mobile networks may need your own TURN server.')
