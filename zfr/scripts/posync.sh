#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
# Thin wrapper — prefer `zfr translate --sync` / import translate.sync.
set -e
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -c 'from translate.sync import sync_catalogs; import sys; raise SystemExit(sync_catalogs())'
