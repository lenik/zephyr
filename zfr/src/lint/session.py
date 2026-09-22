# SPDX-License-Identifier: AGPL-3.0-or-later
"""Thin lint/ize session: options + lazy mesondoc AST cache."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lint.editlist import EditList


@dataclass
class Session:
    """Shared context for a lint or ize run.

    Prefer passing *files* into rules; use the session only for options and
    meson ASTs.
    """

    root: Path
    lang: str = "unknown"
    role: str = "app"
    l10n_level: str = "L1"
    name: str = ""
    dry_run: bool = False
    verbose: bool = False
    do_man: bool = True
    do_subst: bool = True
    do_mesonize: bool = True
    do_commit: bool = False
    author: str | None = None
    # Extra free-form options (lint/ize CLI flags, etc.)
    options: dict[str, Any] = field(default_factory=dict)

    _meson: dict[str, Any] = field(default_factory=dict, repr=False)
    dirty_meson: set[str] = field(default_factory=set)

    def rel(self, path: Path | str) -> str:
        p = Path(path)
        if p.is_absolute():
            try:
                return str(p.relative_to(self.root)).replace("\\", "/")
            except ValueError:
                return str(p).replace("\\", "/")
        return str(p).replace("\\", "/")

    def abspath(self, rel: str | Path) -> Path:
        return self.root / str(rel).lstrip("/")

    def meson_doc(self, rel: str = "meson.build") -> Any:
        """Return a mesondoc ``BuildDoc`` for *rel*, parsing once per session."""
        key = rel.replace("\\", "/").lstrip("/")
        if key not in self._meson:
            try:
                from mesondoc import parse_file
            except ImportError as e:
                raise RuntimeError(
                    "mesondoc is required for meson AST access "
                    "(install python3-mesondoc)"
                ) from e
            path = self.root / key
            result = parse_file(str(path))
            if result.root is None:
                errs = "; ".join(str(e) for e in result.errors) or "parse failed"
                raise RuntimeError(f"mesondoc failed to parse {key}: {errs}")
            self._meson[key] = result.root
        return self._meson[key]

    def mark_meson_dirty(self, rel: str = "meson.build") -> None:
        key = rel.replace("\\", "/").lstrip("/")
        self.dirty_meson.add(key)
        # ensure loaded
        if key not in self._meson and (self.root / key).is_file():
            self.meson_doc(key)

    def set_meson_doc(self, rel: str, doc: Any) -> None:
        key = rel.replace("\\", "/").lstrip("/")
        self._meson[key] = doc
        self.dirty_meson.add(key)

    def flush_meson(self) -> EditList:
        """Serialize dirty meson ASTs to whole-file writes."""
        edits = EditList()
        if not self.dirty_meson:
            return edits
        try:
            from mesondoc.print import format_preserve as _fmt
        except ImportError:
            from mesondoc.print.printer import format_build as _fmt  # type: ignore

        for key in sorted(self.dirty_meson):
            doc = self._meson.get(key)
            if doc is None:
                continue
            try:
                text = _fmt(getattr(doc, "source", "") or "", doc)
            except TypeError:
                text = _fmt(doc)  # type: ignore[misc]
            if not text.endswith("\n"):
                text += "\n"
            edits.write(key, text, detail="meson AST flush", rule="mesondoc")
            if hasattr(doc, "dirty"):
                doc.dirty = False
        self.dirty_meson.clear()
        return edits
