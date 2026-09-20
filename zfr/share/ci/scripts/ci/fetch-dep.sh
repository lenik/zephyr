#!/usr/bin/env bash
# Download prebuilt dependency packages from another project's GitHub Release.
# Never builds the dependency — install-only.
#
# Usage: fetch-dep.sh <owner/repo> <family> <release> <arch> <outdir>
# Env:
#   DEP_TAG   optional release tag (default: latest release)
#   GH_TOKEN  optional (needed for private repos)
set -euo pipefail

REPO=${1:?owner/repo}
FAMILY=${2:?family}          # debian | el
RELEASE=${3:?release}        # bookworm | 9 | ...
ARCH=${4:?arch}
OUTDIR=${5:?outdir}

mkdir -p "$OUTDIR"
OUTDIR=$(cd "$OUTDIR" && pwd)

if [ -n "${DEP_TAG:-}" ]; then
  TAG=$DEP_TAG
else
  TAG=$(gh release list -R "$REPO" -L 20 --json tagName,isLatest,isPrerelease \
    -q '[.[] | select(.isPrerelease|not) | .tagName][0]')
fi
if [ -z "$TAG" ]; then
  echo "fetch-dep: no release tag found for $REPO" >&2
  exit 1
fi

PATTERN="${REPO##*/}-${FAMILY}-${RELEASE}-${ARCH}.zip"
echo "fetch-dep: $REPO@$TAG → $PATTERN"
gh release download "$TAG" -R "$REPO" -D "$OUTDIR" -p "$PATTERN"
unzip -o -q "$OUTDIR/$PATTERN" -d "$OUTDIR"
rm -f "$OUTDIR/$PATTERN"
# Keep only installable packages for the build container.
find "$OUTDIR" -type f ! \( -name '*.deb' -o -name '*.rpm' \) -delete
echo "fetch-dep: ready in $OUTDIR"
ls -la "$OUTDIR"
