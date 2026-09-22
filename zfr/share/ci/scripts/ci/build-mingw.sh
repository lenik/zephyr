#!/usr/bin/env bash
# Build MinGW-w64 artifacts + NuGet package id "<name>.gnu".
# Usage: build-mingw.sh [outdir]
set -euo pipefail

OUTDIR=${1:-"dist/mingw-x64"}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
NAME=$(basename "$ROOT")
MINGW_DIR="$ROOT/packaging/win32/mingw"

mkdir -p "$OUTDIR"
OUTDIR=$(cd "$OUTDIR" && pwd)

if [ ! -d "$MINGW_DIR" ]; then
  echo "build-mingw: missing $MINGW_DIR" >&2
  exit 1
fi

export PATH="$ROOT/scripts/ci:$PATH"
make -C "$MINGW_DIR" clean || true
make -C "$MINGW_DIR" local RID=win-x64

shopt -s nullglob
copied=0
for f in "$MINGW_DIR"/out/*; do
  [ -f "$f" ] || continue
  cp -a "$f" "$OUTDIR/"
  copied=$((copied + 1))
done
shopt -u nullglob

if [ "$copied" -eq 0 ]; then
  echo "build-mingw: no artifacts in $MINGW_DIR/out" >&2
  exit 1
fi

(
  cd "$OUTDIR"
  zip -q -r "${NAME}-mingw-x64.zip" ./*
)
echo "build-mingw: wrote $copied artifact(s) → $OUTDIR"
