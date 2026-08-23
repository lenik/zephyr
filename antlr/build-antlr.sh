#!/bin/bash
# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

set -euo pipefail

classes=$1
grammar=$2
main=$3
commons=$4
out=$5
javac=$6
jar=$7
antlr4=$8

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

gen=$classes/gen
rm -rf "$classes"
mkdir -p "$gen"
"$antlr4" -visitor -o "$gen" "$grammar"
mapfile -t gen_src < <(find "$gen" -name '*.java' -print | sort)
"$javac" -encoding UTF-8 -cp "$runtime:$gen" -d "$classes" "${gen_src[@]}" "$commons" "$main"
"$jar" --create --file "$out" -C "$classes" .
