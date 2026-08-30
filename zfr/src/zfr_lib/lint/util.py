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
from ..i18n import _
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
    src = next((s for s in stanzas if "Source" in s), stanzas[0] if stanzas else {})
    pkg = next((s for s in stanzas if "Package" in s), {})
    return src, pkg, text


def _specs(root: Path) -> list[Path]:
    from ..packaging import resolve_rpm_dir

    found: list[Path] = []
    rpm = resolve_rpm_dir(root)
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


def _stem_is_example_shared(stem: str) -> bool:
    """Exact commons / common_lib example-shared stems."""
    if stem in _EXAMPLE_SHARED_STEMS:
        return True
    return stem.lower() in {s.lower() for s in _EXAMPLE_SHARED_STEMS}


def _stem_is_example_shared_or_test(stem: str) -> bool:
    """Example-shared stems plus unit-test names (commons_test, test_commons, …)."""
    if _stem_is_example_shared(stem):
        return True
    low = stem.lower().replace("-", "_")
    for marker in ("commons", "common_lib", "commonlib"):
        if marker in low:
            return True
    return False


def is_example_shared_src(root: Path, path: Path) -> bool:
    """True for template example shared modules (src/common_lib.*, src/commons.*)."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    if len(rel.parts) != 2 or rel.parts[0] != "src":
        return False
    return _stem_is_example_shared(path.stem)


def is_example_shared_rel(rel: Path) -> bool:
    """True if a template-relative path is example commons scaffolding (src or tests)."""
    if not rel.parts:
        return False
    top = rel.parts[0]
    if top not in {"src", "tests", "lib"}:
        return False
    return _stem_is_example_shared_or_test(rel.stem)


def find_example_shared_modules(root: Path) -> list[Path]:
    src = root / "src"
    if not src.is_dir():
        return []
    found: list[Path] = []
    for path in sorted(src.iterdir()):
        if path.is_file() and _stem_is_example_shared(path.stem):
            found.append(path)
    return found


def _line_of(text: str, needle: str) -> int | None:
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return None


# import * must re-export underscore helpers used by check modules.
__all__ = [n for n in globals() if not n.startswith("__")]
