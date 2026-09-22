# SPDX-License-Identifier: AGPL-3.0-or-later
"""Adapt release-packages.yml when the package is not the git root (monorepo)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def git_toplevel(path: Path) -> Path | None:
    """Return ``git rev-parse --show-toplevel`` for *path*, or None."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(out) if out else None


def package_rel_from_git(package_root: Path, git_root: Path | None = None) -> str:
    """Posix relative path from git root to package (``.`` when same)."""
    top = git_root or git_toplevel(package_root)
    if top is None:
        return "."
    try:
        rel = package_root.resolve().relative_to(top.resolve())
    except ValueError:
        return "."
    s = rel.as_posix()
    return s if s and s != "." else "."


def adapt_workflow_for_package_dir(text: str, pkg_rel: str) -> str:
    """Inject ``working-directory`` and fix ``CI_DEPS_DIR`` for a nested package.

    When *pkg_rel* is ``.``, return *text* unchanged (standalone repo).
    """
    if not pkg_rel or pkg_rel in (".", ""):
        return text
    # Already adapted?
    if f"working-directory: {pkg_rel}" in text:
        # still refresh CI_DEPS_DIR
        pass
    else:
        # Insert global defaults after permissions / concurrency block, before jobs:
        defaults = (
            f"\ndefaults:\n"
            f"  run:\n"
            f"    working-directory: {pkg_rel}\n"
        )
        if re.search(r"^defaults:\s*$", text, re.M):
            text = re.sub(
                r"(^defaults:\n(?:  .*\n)*)",
                defaults.lstrip("\n"),
                text,
                count=1,
                flags=re.M,
            )
        else:
            text = re.sub(
                r"(^concurrency:.*\n(?:  .*\n)*)",
                r"\1" + defaults,
                text,
                count=1,
                flags=re.M,
            )
        # mingw job already has defaults.run.shell — merge working-directory
        text = re.sub(
            r"(mingw:\n(?:.*\n)*?    defaults:\n      run:\n)"
            r"(        shell: msys2 \{0\}\n)",
            rf"\1        working-directory: {pkg_rel}\n\2",
            text,
            count=1,
        )

    # CI_DEPS_DIR must live under the package dir when scripts mkdir ci-deps there
    text = text.replace(
        "CI_DEPS_DIR: ${{ github.workspace }}/ci-deps",
        f"CI_DEPS_DIR: ${{{{ github.workspace }}}}/{pkg_rel}/ci-deps",
    )
    return text


def resolve_workflow_path(package_root: Path) -> Path | None:
    """Prefer package-local workflow, else git-root workflow (monorepo)."""
    local = package_root / ".github" / "workflows" / "release-packages.yml"
    if local.is_file():
        return local
    top = git_toplevel(package_root)
    if top is not None and top.resolve() != package_root.resolve():
        remote = top / ".github" / "workflows" / "release-packages.yml"
        if remote.is_file():
            return remote
    return None
