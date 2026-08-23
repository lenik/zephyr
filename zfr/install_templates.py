#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Meson install helper: copy sibling language templates into share/zephyr."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Keep in sync with meson.build exclude_directories / exclude_files.
EXCLUDE_DIRS = {
    ".cache",
    ".cursor",
    ".git",
    ".hg",
    ".svn",
    ".vscode",
    "__pycache__",
    "bin",
    "build",
    "builddir",
    "cargo-target",
    "dist",
    "rpmbuild",
    "meson-info",
    "meson-logs",
    "meson-private",
    "node_modules",
    "obj",
    "target",
}
EXCLUDE_FILES = {
    "CLAUDE.md",
}
# zfr is installed from this project; do not copy it as a language template.
SKIP_TOP = EXCLUDE_DIRS | {"zfr"}


def _ignore(directory: str, names: list[str]) -> list[str]:
    drop: list[str] = []
    for name in names:
        path = Path(directory) / name
        if name in EXCLUDE_DIRS and path.is_dir():
            drop.append(name)
        elif name in EXCLUDE_FILES:
            drop.append(name)
    return drop


def main() -> int:
    src = Path(sys.argv[1])
    rel = Path(sys.argv[2])
    dest = Path(os.environ["MESON_INSTALL_DESTDIR_PREFIX"]) / rel
    dest.mkdir(parents=True, exist_ok=True)
    for child in sorted(src.iterdir()):
        if not child.is_dir() or child.name in SKIP_TOP or child.name.startswith("."):
            continue
        if not (child / "meson.build").is_file():
            continue
        target = dest / child.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(child, target, ignore=_ignore, symlinks=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
