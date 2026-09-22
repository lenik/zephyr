#!/usr/bin/env bash
# Build native Windows UCRT (MSVC) artifacts + NuGet package.
# Usage: build-ucrt.sh <arch> [outdir]
#   arch: x64 | arm64
set -euo pipefail

ARCH=${1:?arch x64|arm64}
OUTDIR=${2:-"dist/ucrt-${ARCH}"}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
NAME=$(basename "$ROOT")
UCRT_DIR="$ROOT/packaging/win32/ucrt"

case "$ARCH" in
  x64|amd64) ARCH=x64; RID=win-x64 ;;
  arm64|aarch64) ARCH=arm64; RID=win-arm64 ;;
  *) echo "build-ucrt: unsupported arch $ARCH" >&2; exit 1 ;;
esac

mkdir -p "$OUTDIR"
OUTDIR=$(cd "$OUTDIR" && pwd)

if [ ! -d "$UCRT_DIR" ]; then
  echo "build-ucrt: missing $UCRT_DIR" >&2
  exit 1
fi

export PATH="$ROOT/scripts/ci:$PATH"
make -C "$UCRT_DIR" clean || true
make -C "$UCRT_DIR" local ARCH="$ARCH" RID="$RID"

shopt -s nullglob
copied=0
for f in "$UCRT_DIR"/out/*; do
  [ -f "$f" ] || continue
  cp -a "$f" "$OUTDIR/"
  copied=$((copied + 1))
done
shopt -u nullglob

if [ "$copied" -eq 0 ]; then
  echo "build-ucrt: no artifacts in $UCRT_DIR/out" >&2
  exit 1
fi

(
  cd "$OUTDIR"
  zip -q -r "${NAME}-ucrt-${ARCH}.zip" ./*
)
echo "build-ucrt: wrote $copied artifact(s) → $OUTDIR"
