#!/usr/bin/env bash
# Backward compatible alias for v0.1 installations.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec ./run.sh "$@"
