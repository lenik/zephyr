#!/usr/bin/env bash
# Install release CI scaffold into a project tree from zfr share/ci.
# Used by create/ize; safe to run standalone.
#
# Scripts → $DEST/scripts/ci
# Workflow → git toplevel .github/workflows/ (Actions only reads repo root).
# When $DEST is nested under the git root, inject working-directory.
set -euo pipefail
DEST=${1:?dest}
DEST=$(cd "$DEST" && pwd)
HERE=$(cd "$(dirname "$0")" && pwd)
SHARE=$(cd "$HERE/../.." && pwd)
if [ ! -d "$SHARE/.github/workflows" ]; then
  SHARE=$(cd "$HERE/../.." && pwd)
fi

install -d "$DEST/scripts/ci"
for f in matrix.json matrix-from-json.sh build-deb.sh build-rpm.sh \
         build-mingw.sh build-ucrt.sh pack-nuget.py filter-build-depends.py patch-py39-aliases.py \
         submit-windows-packages.sh \
         publish-private.sh fetch-dep.sh deps.conf.example; do
  src="$SHARE/scripts/ci/$f"
  [ -e "$src" ] || continue
  mode=644
  case "$f" in *.sh) mode=755 ;; esac
  install -m "$mode" "$src" "$DEST/scripts/ci/$f"
done

GIT_ROOT=$(git -C "$DEST" rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$GIT_ROOT" ]; then
  GIT_ROOT=$DEST
fi
PKG_REL=
if [ "$DEST" = "$GIT_ROOT" ]; then
  PKG_REL=.
else
  PKG_REL=$(realpath --relative-to="$GIT_ROOT" "$DEST" 2>/dev/null || python3 -c \
    "import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))" "$DEST" "$GIT_ROOT")
fi

install -d "$GIT_ROOT/.github/workflows"
WF_SRC="$SHARE/.github/workflows/release-packages.yml"
WF_DST="$GIT_ROOT/.github/workflows/release-packages.yml"
if [ "$PKG_REL" = "." ]; then
  install -m 644 "$WF_SRC" "$WF_DST"
else
  # Adapt YAML for nested package (working-directory + CI_DEPS_DIR).
  python3 - "$WF_SRC" "$WF_DST" "$PKG_REL" <<'PY'
import sys
from pathlib import Path
src, dst, pkg = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
text = src.read_text(encoding="utf-8")
# Prefer in-tree helper when PYTHONPATH includes zfr src
try:
    from lint.ci_paths import adapt_workflow_for_package_dir
    text = adapt_workflow_for_package_dir(text, pkg)
except Exception:
    if f"working-directory: {pkg}" not in text:
        insert = f"\ndefaults:\n  run:\n    working-directory: {pkg}\n"
        if "concurrency:" in text:
            # after concurrency block
            import re
            text = re.sub(
                r"(concurrency:.*?(?:\n  .*)*\n)",
                r"\1" + insert,
                text,
                count=1,
                flags=re.S,
            )
        else:
            text = insert + text
    text = text.replace(
        "CI_DEPS_DIR: ${{ github.workspace }}/ci-deps",
        f"CI_DEPS_DIR: ${{{{ github.workspace }}}}/{pkg}/ci-deps",
    )
    # mingw defaults.run.shell — add working-directory
    if f"working-directory: {pkg}" not in text.split("mingw:")[-1][:400]:
        text = text.replace(
            "    defaults:\n      run:\n        shell: msys2 {0}\n",
            f"    defaults:\n      run:\n        working-directory: {pkg}\n"
            f"        shell: msys2 {{0}}\n",
            1,
        )
dst.write_text(text, encoding="utf-8")
PY
fi

# Remove nested package .github that Actions would ignore
if [ "$PKG_REL" != "." ] && [ -f "$DEST/.github/workflows/release-packages.yml" ]; then
  rm -f "$DEST/.github/workflows/release-packages.yml"
  rmdir "$DEST/.github/workflows" 2>/dev/null || true
  rmdir "$DEST/.github" 2>/dev/null || true
fi

echo "ci-scaffold: scripts → $DEST/scripts/ci; workflow → $WF_DST (pkg=$PKG_REL)"
