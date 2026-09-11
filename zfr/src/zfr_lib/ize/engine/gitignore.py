# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize helpers for project-root .gitignore (track .cursor/rules)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Ize

# Lines that ignore the whole .cursor tree (block shipping cursor-rules).
_CURSOR_IGNORE_RE = re.compile(
    r"^\s*(?:/\.cursor/?|\.cursor/?|\.cursor/\*|\.cursor/\*\*)\s*(?:#.*)?$"
)


def ensure_gitignore_tracks_cursor(ize: "Ize") -> None:
    """Remove ``.cursor`` ignore rules so ``.cursor/rules`` can be committed.

    Templates historically ignored ``.cursor/``; zephyr style commits the
    shipped rules. Callers should ``git add -f .cursor/`` after install.
    """
    path = ize.root / ".gitignore"
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    removed = 0
    for line in lines:
        if _CURSOR_IGNORE_RE.match(line.rstrip("\n")):
            removed += 1
            continue
        kept.append(line)
    if not removed:
        return
    new = "".join(kept)
    if not new.endswith("\n") and new:
        new += "\n"
    rel = ".gitignore"
    if ize.dry_run:
        ize.note(
            "would-update",
            rel,
            f"drop {removed} .cursor ignore line(s)",
            rule="ize.stdfiles",
        )
        return
    ize.write_text(path, new, f"drop {removed} .cursor ignore line(s)")
