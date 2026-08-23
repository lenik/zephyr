#!/bin/bash
# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
bin="${1:?usage: run_fixtures.sh /path/to/some_puff1}"

failures=0

check() {
    local name=$1
    local input=$2
    local expect=$3
    local extra=${4:-}
    local got want
    got=$(cd "$root" && "$bin" $extra < "$root/$input")
    want=$(cat "$root/$expect")
    if [ "$got" != "$want" ]; then
        echo "FAIL $name" >&2
        echo "got:" >&2
        printf '%s\n' "$got" >&2
        echo "want:" >&2
        printf '%s\n' "$want" >&2
        failures=$((failures + 1))
    fi
}

check format-hello tests/fixtures/hello.sexpr tests/expected/hello.format
check format-add tests/fixtures/add.sexpr tests/expected/add.format
check dump-hello tests/fixtures/hello.sexpr tests/expected/hello.dump --dump

exit "$failures"
