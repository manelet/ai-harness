#!/bin/sh
set -eu
HARNESS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$HARNESS_ROOT/scripts/install.py" "$@"
