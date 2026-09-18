#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# DESTDIR preview install (meson run_target look).
set -euo pipefail
SOURCE_ROOT="${1:-${MESON_SOURCE_ROOT:-.}}"
BUILD_ROOT="${2:-${MESON_BUILD_ROOT:-.}}"
tmpdir=$(mktemp -d)
trap 'rm -fr "$tmpdir"' EXIT
DESTDIR="$tmpdir" meson install -C "$BUILD_ROOT"
tree -L 6 -I po "$tmpdir" 2>/dev/null || (cd "$tmpdir" && find -maxdepth 6 -name po -prune -o -print)
