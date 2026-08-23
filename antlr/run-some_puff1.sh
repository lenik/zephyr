#!/bin/bash
# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

set -euo pipefail

java_bin=$1
jar=$2
out=$3

runtime=""
for cand in /usr/share/java/antlr4-runtime.jar /usr/share/java/antlr4-runtime-*.jar; do
    if [ -f "$cand" ]; then
        runtime=$cand
        break
    fi
done

if [ -z "$runtime" ]; then
    echo "antlr runtime jar not found under /usr/share/java" >&2
    exit 1
fi

cat >"$out" <<EOF
#!/usr/bin/env sh
exec "$java_bin" -cp "$jar:$runtime" Main "\$@"
EOF
chmod +x "$out"
