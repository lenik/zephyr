#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
# Thin wrapper — prefer `zfr build --look` / import build_look.
set -e
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
BUILD="${1:-$ROOT/build}"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -c 'from build_look import look_install; from pathlib import Path; import sys; raise SystemExit(look_install(Path(sys.argv[1]), builddir=Path(sys.argv[2])))' "$ROOT" "$BUILD"
