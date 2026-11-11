#!/usr/bin/env bash
# FACO Crumble Linux installer + Program Doctor: FAST / STANDARD / FULL AUDIT.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
MODE=FAST; CHECK_ONLY=0; NO_LAUNCH=0; NONINTERACTIVE=0; PREFIX=''; RUN_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --standard) MODE=STANDARD; shift ;;
    --full-audit) MODE=FULL; shift ;;
    --check-only) CHECK_ONLY=1; shift ;;
    --no-launch) NO_LAUNCH=1; shift ;;
    --noninteractive) NONINTERACTIVE=1; shift ;;
    --prefix) [[ $# -gt 1 ]] || { echo '--prefix requires a path' >&2; exit 2; }; PREFIX="$2"; shift 2 ;;
    --local|--quick|--no-open|--domain|--public-port|--admin-port)
      flag="$1"; RUN_ARGS+=("$flag"); shift
      case "$flag" in --domain|--public-port|--admin-port) [[ $# -gt 0 ]] || { echo "$flag requires a value" >&2; exit 2; }; RUN_ARGS+=("$1"); shift ;; esac ;;
    *) echo "Unknown install flag: $1" >&2; exit 2 ;;
  esac
done
printf '%s\n' "FACO Crumble v0.6.2 • ${MODE} Program Doctor + Linux installation" '============================================================'
python3 - <<'PY'
import sys
print('Python:',sys.version.split()[0])
assert sys.version_info >= (3,10), 'Python 3.10+ required'
PY
for file in server.py launcher.py public/index.html public/app.js public/style.css public/favicon.svg admin/index.html admin/admin.css admin/admin.js scripts/install_linux.py run.sh; do
  if [[ ! -f "$file" || -L "$file" ]]; then echo "FAIL: Missing/symlinked $file" >&2; exit 1; fi
done
python3 - <<'PY_AST'
import ast
from pathlib import Path
for name in ('server.py','launcher.py','scripts/doctor.py','scripts/install_linux.py'):
    ast.parse(Path(name).read_text(encoding='utf8'), filename=name)
print('Python syntax: Passed (no bytecode files written)')
PY_AST
if command -v node >/dev/null 2>&1; then
  node --check public/app.js
  node --check admin/admin.js
  echo 'JavaScript syntax: Passed'
else
  echo 'NOTE: Node unavailable; JS syntax not audited.'
fi
if command -v cloudflared >/dev/null 2>&1; then
  cloudflared --version | head -n 1
else
  echo 'Cloudflare optional: supply cloudflared via PATH, ~/.local/bin or FACO_CLOUDFLARED.'
fi
if [[ "$MODE" != FAST ]]; then
  echo 'Running STANDARD regressions.'
  python3 -m unittest discover -s tests -p 'test_signaling.py' -v
  python3 -m unittest discover -s tests -p 'test_video_signaling.py' -v
  python3 -m unittest discover -s tests -p 'test_tunnel.py' -v
  python3 -m unittest discover -s tests -p 'test_linux_install.py' -v
  python3 -m unittest discover -s tests -p 'test_process_smoke.py' -v
  if command -v node >/dev/null 2>&1; then
    node tests/test_client_mock.cjs
    node tests/test_admin_mock.cjs
  fi
fi
if [[ "$MODE" == FULL ]]; then
  python3 - <<'PY'
from pathlib import Path
from xml.etree import ElementTree as ET
root=Path.cwd()
for p in (root/'public/favicon.svg', *sorted((root/'assets').glob('*.svg'))):
    ET.parse(p)
    print('Vector logo:',p.name,'VALID SVG')
source=(root/'public/app.js').read_text()
assert 'localStorage.setItem' not in source and 'sessionStorage.setItem' not in source, 'Call client must not persist credentials'
assert 'infinityFlow' in (root/'public/style.css').read_text(), 'Missing active-call infinity'
assert "'version': '0.6.2'" in (root/'server.py').read_text(), 'Server version mismatch'
installer=(root/'scripts/install_linux.py').read_text()
assert 'XDG_DATA_HOME' in installer and 'XDG_STATE_HOME' in installer and 'XDG_CONFIG_HOME' in installer
for path in (root/'run.sh', root/'launcher.py', root/'scripts/install_linux.py'):
    assert '/media/owner/' not in path.read_text(), 'Public installer contains private workstation path'
print('Full audit passed: SVG, privacy, animation, XDG Linux paths, version wiring')
PY
fi
printf '%s\n' "${MODE} preflight passed; no system packages modified."
if [[ "$CHECK_ONLY" == 1 ]]; then exit 0; fi
chmod +x install.sh run.sh start.sh launcher.py scripts/install_linux.py
args=()
[[ -z "$PREFIX" ]] || args+=(--prefix "$PREFIX")
[[ "$NONINTERACTIVE" == 0 ]] || args+=(--noninteractive)
installed_output="$(python3 scripts/install_linux.py "${args[@]}")"
printf '%s\n' "$installed_output"
installed_path="$(printf '%s\n' "$installed_output" | sed -n 's/^FACO_INSTALLED_PATH=//p' | tail -n 1)"
[[ -n "$installed_path" && -x "$installed_path/run.sh" ]] || { echo 'Installer did not return a runnable app.' >&2; exit 1; }
if [[ "$NO_LAUNCH" == 1 ]]; then exit 0; fi
if [[ -t 0 ]]; then read -r -p 'Press Enter to launch FACO Crumble (Ctrl+C cancels): ' _; fi
exec "$installed_path/run.sh" "${RUN_ARGS[@]}"
