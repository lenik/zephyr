#!/bin/sh
# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later
set -eu
cd "$(dirname "$0")/.."
command -v cobc >/dev/null 2>&1 || { echo 'skip: cobc not installed'; exit 0; }
cobc -x -I src -o /tmp/test_commons-cobol src/some_puff1.cob
echo ok
