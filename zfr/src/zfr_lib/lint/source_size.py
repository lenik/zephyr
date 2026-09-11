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

# Documentation and shell completions are not subject to source.long (ZL001).
_DOC_OR_COMPLETION_SUFFIXES = {".adoc", ".md", ".txt", ".rst", ".bash"}
_DOC_OR_COMPLETION_NAMES = {
    "README",
    "README.md",
    "README-zh.md",
    "README-zh_CN.md",
    "CHANGELOG",
    "CHANGELOG.md",
    "NEWS",
    "NEWS.md",
}


def _count_lines(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _line in fh)
    except OSError:
        return 0


def _is_doc_or_completion(rel: str, path: Path) -> bool:
    """True for README/man/docs and bash-completion scripts (length not linted)."""
    parts = Path(rel).parts
    if not parts:
        return False
    if parts[0] in {"docs", "completions", "man"}:
        return True
    name = path.name
    if name in _DOC_OR_COMPLETION_NAMES or name.startswith("README"):
        return True
    if path.suffix.lower() in _DOC_OR_COMPLETION_SUFFIXES:
        # Root or tools/*.bash completion; docs/*.adoc; any *.md under tree.
        if path.suffix.lower() == ".bash":
            return True
        if path.suffix.lower() in {".adoc", ".md", ".rst", ".txt"}:
            return True
    return False


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
    if _is_doc_or_completion(rel, path):
        return False
    return rel.startswith(_SOURCE_PREFIXES)


def _extract_subdir_fix(rel: str) -> str:
    path = Path(rel)
    subdir = (path.parent / path.stem).as_posix() + "/"
    example = f"{subdir}{path.stem}_part.py"
    return _(
        "Extract cohesive sections into package subdirectory %(subdir)s "
        "(e.g. %(example)s) and keep a thin %(rel)s entry point."
    ) % {"subdir": subdir, "example": example, "rel": rel}


def check_source_size(root: Path, role: str) -> list[Finding]:
    if role == "meta":
        return []
    out: list[Finding] = []
    for path in iter_files(root):
        if not _is_source_candidate(root, path):
            continue
        lines = _count_lines(path)
        rel = _rel(root, path)
        warn_limit = 2000 if path.suffix == ".java" else _WARN_LINES
        if lines > warn_limit:
            out.append(
                Finding(
                    "warn",
                    "source.long",
                    _("%(rel)s is %(lines)d lines (>%(limit)d); file is very long")
                    % {"rel": rel, "lines": lines, "limit": warn_limit},
                    rel,
                    line=warn_limit + 1,
                    fix=_extract_subdir_fix(rel),
                )
            )
        elif lines > _NOTE_LINES:
            out.append(
                Finding(
                    "note",
                    "source.long",
                    _("%(rel)s is %(lines)d lines (>%(limit)d); consider splitting soon")
                    % {"rel": rel, "lines": lines, "limit": _NOTE_LINES},
                    rel,
                    line=_NOTE_LINES + 1,
                    fix=_extract_subdir_fix(rel),
                )
            )
    if not any(f.severity == "warn" and f.code == "source.long" for f in out):
        out.append(Finding("ok", "source.size", _("no oversized source files")))
    return out
