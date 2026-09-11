# SPDX-License-Identifier: AGPL-3.0-or-later
"""Minimal gitignore-style matcher for ``.tarignore``."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class _Pat:
    raw: str
    regex: re.Pattern[str]
    negate: bool
    dir_only: bool


def _compile_line(line: str) -> _Pat | None:
    raw = line.rstrip("\n\r")
    if not raw.strip() or raw.lstrip().startswith("#"):
        return None
    negate = False
    body = raw
    if body.startswith("!"):
        negate = True
        body = body[1:]
    dir_only = body.endswith("/")
    if dir_only:
        body = body[:-1]
    if not body:
        return None
    anchored = body.startswith("/")
    if anchored:
        body = body[1:]
    # Translate gitignore glob → regex (supports *, ?, **, and leading anchor).
    i = 0
    out: list[str] = []
    while i < len(body):
        c = body[i]
        if c == "*" and i + 1 < len(body) and body[i + 1] == "*":
            if i + 2 < len(body) and body[i + 2] == "/":
                out.append("(?:.*/)?")
                i += 3
            else:
                out.append(".*")
                i += 2
            continue
        if c == "*":
            out.append("[^/]*")
            i += 1
            continue
        if c == "?":
            out.append("[^/]")
            i += 1
            continue
        if c == "/":
            out.append("/")
            i += 1
            continue
        out.append(re.escape(c))
        i += 1
    core = "".join(out)
    if anchored:
        pattern = f"^{core}(?:/.*)?$" if not dir_only else f"^{core}$|^{core}/.*"
    else:
        pattern = f"(?:^|/){core}(?:/.*)?$" if not dir_only else f"(?:^|/){core}$|(?:^|/){core}/.*"
    return _Pat(raw=raw, regex=re.compile(pattern), negate=negate, dir_only=dir_only)


class TarIgnore:
    """gitignore-like rules loaded from ``.tarignore`` (and optional extras)."""

    def __init__(self, patterns: list[_Pat] | None = None) -> None:
        self._patterns = list(patterns or [])

    @classmethod
    def from_text(cls, text: str) -> TarIgnore:
        pats: list[_Pat] = []
        for line in text.splitlines():
            p = _compile_line(line)
            if p is not None:
                pats.append(p)
        return cls(pats)

    @classmethod
    def load(cls, root: Path) -> TarIgnore:
        path = root / ".tarignore"
        if not path.is_file():
            return cls()
        try:
            return cls.from_text(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            return cls()

    def __bool__(self) -> bool:
        return bool(self._patterns)

    def match(self, rel: str, *, is_dir: bool = False) -> bool:
        """True when *rel* (posix, no leading ``./``) should be ignored."""
        rel = rel.replace("\\", "/").lstrip("./")
        if not rel:
            return False
        ignored = False
        for pat in self._patterns:
            if pat.dir_only and not is_dir and "/" not in rel.rstrip("/"):
                # dir-only pattern: also matches paths under that directory
                if not pat.regex.search(rel) and not pat.regex.search(rel + "/"):
                    continue
            if pat.regex.search(rel) or (is_dir and pat.regex.search(rel.rstrip("/") + "/")):
                ignored = not pat.negate
        return ignored
