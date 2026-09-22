#!/usr/bin/env bash
# Install release CI scaffold into a project tree from zfr share/ci.
# Used by create/ize; safe to run standalone.
set -euo pipefail
DEST=${1:?dest}
HERE=$(cd "$(dirname "$0")" && pwd)
# Prefer sibling share next to this script when running from checkout:
#   zfr/share/ci/scripts/ci/install-ci-scaffold.sh
SHARE=$(cd "$HERE/../.." && pwd)
if [ ! -d "$SHARE/.github/workflows" ]; then
  # Installed: $prefix/share/zephyr/ci/...
  SHARE=$(cd "$HERE/../.." && pwd)
fi
install -d "$DEST/.github/workflows" "$DEST/scripts/ci"
install -m 644 "$SHARE/.github/workflows/release-packages.yml" \
  "$DEST/.github/workflows/release-packages.yml"
for f in matrix.json matrix-from-json.sh build-deb.sh build-rpm.sh \
         build-mingw.sh build-ucrt.sh pack-nuget.py \
         submit-windows-packages.sh \
         publish-private.sh fetch-dep.sh deps.conf.example; do
  src="$SHARE/scripts/ci/$f"
  [ -e "$src" ] || continue
  mode=644
  case "$f" in *.sh) mode=755 ;; esac
  install -m "$mode" "$src" "$DEST/scripts/ci/$f"
done
echo "ci-scaffold: installed under $DEST"
