# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source file length checks."""

from __future__ import annotations

from pathlib import Path

from .. import iter_files, is_probably_text
from .finding import Finding
from .util import _rel, is_example_shared_src

_WARN_LINES = 1000
_NOTE_LINES = 600

_SOURCE_PREFIXES = ("src/", "tests/", "apps/", "lib/")


def _count_lines(path: Path) -> int:
    try:
        return sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
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
                    f"{rel} is {lines} lines (>{_WARN_LINES}); file is very long",
                    rel,
                    line=_WARN_LINES + 1,
                    fix="Split this file into smaller modules; keep each unit focused and testable.",
                )
            )
        elif lines > _NOTE_LINES:
            out.append(
                Finding(
                    "note",
                    "source.long",
                    f"{rel} is {lines} lines (>{_NOTE_LINES}); consider modularizing soon",
                    rel,
                    line=_NOTE_LINES + 1,
                    fix="Plan extraction of helpers or submodules before the file grows further.",
                )
            )
    if not any(f.severity in ("warn", "note") and f.code == "source.long" for f in out):
        out.append(Finding("ok", "source.size", "no oversized source files"))
    return out
