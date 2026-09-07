# SPDX-License-Identifier: AGPL-3.0-or-later
"""Canonical standard files: LICENSE, .githooks, .cursor/rules.

Installed by ``zfr create`` and reset by ``zfr ize``. Not part of language
templates.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import pkgdatadir
from .cursor_rules import RULE_NAMES, cursor_rule_src, install_cursor_rules


def license_src() -> Path | None:
    candidates = [
        pkgdatadir() / "LICENSE",
        pkgdatadir() / "std" / "LICENSE",
    ]
    here = Path(__file__).resolve()
    if here.parent.name == "zfr_lib":
        candidates.append(here.parents[2] / "LICENSE")
    for path in candidates:
        if path.is_file():
            return path
    return None


def githooks_pre_commit_src() -> Path | None:
    # Project hook (debian/changelog at tree root). Never use the meta-repo
    # .githooks (that one points at zfr/debian).
    candidates = [
        pkgdatadir() / "githooks" / "pre-commit",
        pkgdatadir() / ".githooks" / "pre-commit",
    ]
    here = Path(__file__).resolve()
    if here.parent.name == "zfr_lib":
        candidates.append(here.parents[2] / "githooks" / "pre-commit")
    for path in candidates:
        if path.is_file():
            return path
    return None


def install_license(dest: Path) -> Path | None:
    src = license_src()
    if src is None:
        return None
    dest_file = dest / "LICENSE"
    shutil.copy2(src, dest_file)
    return dest_file


def install_githooks(dest: Path) -> Path | None:
    src = githooks_pre_commit_src()
    if src is None:
        return None
    hook_dir = dest / ".githooks"
    dest_hook = hook_dir / "pre-commit"
    hook_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_hook)
    dest_hook.chmod(dest_hook.stat().st_mode | 0o111)
    return dest_hook


def install_std_files(dest: Path) -> list[Path]:
    """Install/overwrite LICENSE, .githooks/pre-commit, and cursor rules."""
    installed: list[Path] = []
    for fn in (install_license, install_githooks, install_cursor_rules):
        path = fn(dest)
        if path is not None:
            installed.append(path)
    return installed


def std_file_sources() -> dict[str, Path]:
    """Map relative project paths to canonical sources (existing files only)."""
    out: dict[str, Path] = {}
    lic = license_src()
    if lic is not None:
        out["LICENSE"] = lic
    hook = githooks_pre_commit_src()
    if hook is not None:
        out[".githooks/pre-commit"] = hook
    for name in RULE_NAMES:
        rule = cursor_rule_src(name)
        if rule is not None:
            out[f".cursor/rules/{name}"] = rule
    return out
