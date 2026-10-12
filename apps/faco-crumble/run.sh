#!/usr/bin/env bash
# FACO Crumble portable launcher: OS-standard user paths on ALL Linux installations.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
umask 077
command -v python3 >/dev/null 2>&1 || { echo 'Python 3.10+ required' >&2; exit 1; }
python3 - <<'PY'
import sys
assert sys.version_info >= (3, 10), 'Python 3.10+ required'
PY
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
VENV="${FACO_VENV_PATH:-$DATA_HOME/faco-crumble/venv}"
# A custom env is opt-in, never derived from private workstation mount points.
if [[ -n "${FACO_VENV_PATH:-}" && ! -d "$(dirname "$VENV")" ]]; then
  echo "Configured custom runtime parent is unavailable: $(dirname "$VENV")" >&2
  echo 'Use OS Default Location: unset FACO_VENV_PATH; Cancel Installation: Ctrl+C.' >&2
  exit 1
fi
# Mandatory reuse scan before installing Python packages.
PYTHON=python3
if [[ -x "$VENV/bin/python" ]] && "$VENV/bin/python" -c 'import aiohttp,qrcode' 2>/dev/null; then
  PYTHON="$VENV/bin/python"
  echo "Reusing installed FACO runtime: $VENV"
elif python3 -c 'import aiohttp,qrcode' 2>/dev/null; then
  echo 'Reusing compatible system Python packages.'
else
  # An explicitly configured shared FACO root may be used, but is never required.
  if [[ -n "${FACO_SHARED_ROOT:-}" ]]; then
    SHARED="$FACO_SHARED_ROOT/envs/FACO_Crumble"
    if [[ -x "$SHARED/bin/python" ]] && "$SHARED/bin/python" -c 'import aiohttp,qrcode' 2>/dev/null; then
      PYTHON="$SHARED/bin/python"
      echo "Reusing explicitly selected FACO shared runtime: $SHARED"
    else
      echo "Configured shared FACO runtime not usable: $SHARED" >&2
      echo 'Falling back to OS-default isolated environment. No shared data is changed.'
    fi
  fi
  if [[ "$PYTHON" == python3 ]]; then
    mkdir -p "$(dirname "$VENV")"
    if [[ ! -x "$VENV/bin/python" ]]; then
      echo "Creating runtime environment: $VENV"
      python3 -m venv "$VENV" || { echo 'Install python3-venv for your distribution.' >&2; exit 1; }
    fi
    PYTHON="$VENV/bin/python"
    if ! "$PYTHON" -c 'import aiohttp,qrcode' 2>/dev/null; then
      echo 'Installing Python dependencies in isolated user runtime…'
      "$PYTHON" -m pip install --disable-pip-version-check -r requirements.txt
    fi
  fi
fi
mkdir -p "$STATE_HOME/faco-crumble"
"$PYTHON" scripts/doctor.py
exec "$PYTHON" launcher.py "$@"
