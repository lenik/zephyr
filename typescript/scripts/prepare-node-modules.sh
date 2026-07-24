#!/usr/bin/env bash
# Prepare a classic (npm) production node_modules tree for install / NODE_PATH.
# Usage: prepare-node-modules.sh <project-root> <outdir>
set -euo pipefail

src=$1
outdir=$2

rm -rf "$outdir"
mkdir -p "$outdir"
cp "$src/package.json" "$outdir/package.json"

# npm produces a resolvable layout for NODE_PATH; pnpm's store layout does not.
if command -v npm >/dev/null 2>&1; then
  (cd "$outdir" && npm install --omit=dev --ignore-scripts --no-package-lock)
else
  echo "prepare-node-modules.sh: npm is required to stage production dependencies" >&2
  exit 1
fi

test -d "$outdir/node_modules/node-gettext"
test -d "$outdir/node_modules/gettext-parser"
