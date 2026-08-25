# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source file length checks."""

from __future__ import annotations

from pathlib import Path

from .. import iter_files, is_probably_text
from ..i18n import _
from .finding import Finding
from .util import _rel, is_example_shared_src

_WARN_LINES = 1000
_NOTE_LINES = 600

_SOURCE_PREFIXES = ("src/", "tests/", "apps/", "lib/")


def _count_lines(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _line in fh)
    except OSError:
        return 0


def _is_source_candidate(root: Path, path: Path) -> bool:
    if not path.is_file() or not is_probably_text(path):
        return False
    if is_example_shared_src(root, path):
        return False
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return False
    if rel.startswith("debian/") or rel.startswith("po/") or rel.startswith("docs/"):
        return False
    return rel.startswith(_SOURCE_PREFIXES)


def check_source_size(root: Path, role: str) -> list[Finding]:
    if role == "meta":
        return []
    out: list[Finding] = []
    for path in iter_files(root):
        if not _is_source_candidate(root, path):
            continue
        lines = _count_lines(path)
        rel = _rel(root, path)
        if lines > _WARN_LINES:
            out.append(
                Finding(
                    "warn",
                    "source.long",
                    _("%(rel)s is %(lines)d lines (>%(limit)d); file is very long")
                    % {"rel": rel, "lines": lines, "limit": _WARN_LINES},
                    rel,
                    line=_WARN_LINES + 1,
                    fix=_("Split this file into smaller modules; keep each unit focused and testable."),
                )
            )
        elif lines > _NOTE_LINES:
            out.append(
                Finding(
                    "note",
                    "source.long",
                    _("%(rel)s is %(lines)d lines (>%(limit)d); consider modularizing soon")
                    % {"rel": rel, "lines": lines, "limit": _NOTE_LINES},
                    rel,
                    line=_NOTE_LINES + 1,
                    fix=_("Plan extraction of helpers or submodules before the file grows further."),
                )
            )
    if not any(f.severity in ("warn", "note") and f.code == "source.long" for f in out):
        out.append(Finding("ok", "source.size", _("no oversized source files")))
    return out
