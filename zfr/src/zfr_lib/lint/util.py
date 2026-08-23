# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared helpers for zfr lint checks."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import (
    LANGS,
    RECOMMENDED_I18N_LINGUAS,
    RECOMMENDED_I18N_SOURCE,
    TEMPLATE_PUFF,
    _is_zfr_cli_package,
    _is_zfr_meta_repo,
    changelog_version,
    detect_lang,
    find_project_dir,
    is_probably_text,
    iter_files,
    template_dir,
    version_file_version,
)
from ..csr import Csr
from ..packaging import _meson_project_fields, _parse_control_stanzas
from .finding import Finding
_PLACEHOLDER_README = "THIS FILE IS GENERATED FROM A TEMPLATE"
_PLACEHOLDER_README_ZH = "本文件由模板生成"
_AGPL = "AGPL-3.0-or-later"


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _role(root: Path) -> str:
    from ..shape import resolve_layout

    try:
        return resolve_layout(root).role
    except SystemExit:
        if _is_zfr_meta_repo(root):
            return "meta"
        if _is_zfr_meta_repo(root.parent):
            return "template"
        return "app"


def _control(root: Path) -> tuple[dict[str, str], dict[str, str], str]:
    path = root / "debian" / "control"
    text = _read(path)
    stanzas = _parse_control_stanzas(text) if text else []
    src = stanzas[0] if stanzas else {}
    pkg = stanzas[1] if len(stanzas) > 1 else src
    return src, pkg, text


def _specs(root: Path) -> list[Path]:
    found: list[Path] = []
    rpm = root / "rpm"
    if rpm.is_dir():
        found.extend(sorted(rpm.glob("*.spec")))
    found.extend(sorted(root.glob("*.spec")))
    uniq: list[Path] = []
    seen: set[Path] = set()
    for p in found:
        r = p.resolve()
        if r in seen:
            continue
        seen.add(r)
        uniq.append(p)
    return uniq


def _has_file(root: Path, rel: str) -> bool:
    if (root / rel).is_file():
        return True
    if rel in ("README.md", "README-zh.md") and _is_zfr_cli_package(root):
        return (root.parent / rel).is_file()
    return False


_EXAMPLE_SHARED_STEMS = frozenset({"common_lib", "commons", "Commons", "CommonLib"})


def is_example_shared_src(root: Path, path: Path) -> bool:
    """True for template example shared modules (src/common_lib.*, src/commons.*)."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    if len(rel.parts) != 2 or rel.parts[0] != "src":
        return False
    stem = path.stem
    return stem in _EXAMPLE_SHARED_STEMS or stem.lower() in _EXAMPLE_SHARED_STEMS


def find_example_shared_modules(root: Path) -> list[Path]:
    src = root / "src"
    if not src.is_dir():
        return []
    found: list[Path] = []
    for path in sorted(src.iterdir()):
        if path.is_file() and (
            path.stem in _EXAMPLE_SHARED_STEMS or path.stem.lower() in _EXAMPLE_SHARED_STEMS
        ):
            found.append(path)
    return found


def _line_of(text: str, needle: str) -> int | None:
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return None


# import * must re-export underscore helpers used by check modules.
__all__ = [n for n in globals() if not n.startswith("__")]
