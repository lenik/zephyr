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

# asciidoctor is required by meson.build; gem fallback when pacman package absent.
if ! command -v asciidoctor >/dev/null 2>&1; then
  if command -v gem >/dev/null 2>&1; then
    gem install --no-document asciidoctor || true
    # MSYS2 ruby often installs gems outside PATH.
    gem_bindir=$(ruby -e 'print Gem.bindir' 2>/dev/null || true)
    if [ -n "${gem_bindir:-}" ]; then
      export PATH="$gem_bindir:$PATH"
    fi
    user_bindir=$(ruby -e 'print Gem.user_dir' 2>/dev/null || true)
    if [ -n "${user_bindir:-}" ] && [ -d "$user_bindir/bin" ]; then
      export PATH="$user_bindir/bin:$PATH"
    fi
  fi
fi
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
