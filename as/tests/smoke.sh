#!/bin/bash
# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

set -euo pipefail

bin="${1:?usage: smoke.sh /path/to/some_puff1}"

if ! printf 'hello asm\n' | "$bin" | cmp -s - <(printf 'hello asm\n'); then
    echo "smoke failed" >&2
    exit 1
fi
