#!/usr/bin/env bash
# Build MinGW-w64 artifacts + NuGet package id "<name>.gnu".
# Usage: build-mingw.sh [outdir]
set -euo pipefail

OUTDIR=${1:-"dist/mingw-x64"}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
NAME=$(basename "$ROOT")
if [ -f "$ROOT/debian/control" ]; then
  src=$(sed -n 's/^Source:[[:space:]]*//p' "$ROOT/debian/control" | head -n1 | tr -d '[:space:]')
  [ -n "$src" ] && NAME=$src
fi
MINGW_DIR="$ROOT/packaging/win32/mingw"

mkdir -p "$OUTDIR"
OUTDIR=$(cd "$OUTDIR" && pwd)

if [ ! -d "$MINGW_DIR" ]; then
  echo "build-mingw: missing $MINGW_DIR" >&2
  exit 1
fi

# Prefer MinGW64 python/meson over MSYS usr/bin (avoids broken path mixing).
export PATH="/mingw64/bin:$PATH"
if [ -x /mingw64/bin/python3 ]; then
  export PYTHON=/mingw64/bin/python3
elif [ -x /mingw64/bin/python ]; then
  export PYTHON=/mingw64/bin/python
fi
# Windows runners default to cp1252; PO/i18n sources are UTF-8.
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# asciidoctor is required by meson.build; gem fallback when pacman package absent.
if ! command -v asciidoctor >/dev/null 2>&1; then
  if command -v gem >/dev/null 2>&1; then
    gem install --no-document asciidoctor || true
  fi
fi
for d in \
  "$(ruby -e 'print Gem.bindir' 2>/dev/null || true)" \
  "$(ruby -e 'print Gem.user_dir' 2>/dev/null || true)/bin" \
  $HOME/.local/share/gem/ruby/*/bin
do
  [ -n "$d" ] && [ -d "$d" ] && export PATH="$d:$PATH"
done
if ! command -v asciidoctor >/dev/null 2>&1; then
  echo "build-mingw: asciidoctor not found (install mingw asciidoctor or gem)" >&2
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
