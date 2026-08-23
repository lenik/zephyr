#!/bin/sh
# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later
set -eu
root="$(cd "$(dirname "$0")/.." && pwd)"
build="${MESON_BUILD_ROOT:-$root/build}"
test -x "$build/test_commons" || { echo "missing $build/test_commons"; exit 1; }
(
  cd "$build"
  ./test_commons
)
