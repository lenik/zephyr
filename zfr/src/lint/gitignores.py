# SPDX-License-Identifier: AGPL-3.0-or-later
"""Load and match ``.gitignore`` (and nested) during project scans."""

from __future__ import annotations

from pathlib import Path

from tarignore import TarIgnore, _compile_line, _Pat


class GitIgnoreStack:
    """Stacked gitignore matchers for a walk rooted at *root*.

    Push/pop as the walker enters/leaves directories. Patterns in a nested
    ``.gitignore`` are scoped to that directory (gitignore semantics).
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._stack: list[tuple[str, list[_Pat]]] = []
        # Root .gitignore (and optional parent-repo patterns via git if needed)
        self._push_dir(self.root, "")

    def _push_dir(self, abs_dir: Path, rel_prefix: str) -> None:
        gi = abs_dir / ".gitignore"
        pats: list[_Pat] = []
        if gi.is_file():
            try:
                text = gi.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            for line in text.splitlines():
                p = _compile_line(line)
                if p is not None:
                    pats.append(p)
        self._stack.append((rel_prefix, pats))

    def enter(self, abs_dir: Path, rel_posix: str) -> None:
        """Call when descending into *abs_dir* (posix rel without trailing slash)."""
        prefix = rel_posix.strip("/")
        if prefix:
            prefix = prefix + "/"
        else:
            prefix = ""
        self._push_dir(abs_dir, prefix)

    def leave(self) -> None:
        if self._stack:
            self._stack.pop()

    def ignored(self, rel_posix: str, *, is_dir: bool = False) -> bool:
        """True if *rel_posix* (no leading ``./``) is ignored by any stacked rules."""
        rel = rel_posix.replace("\\", "/").lstrip("./")
        if not rel or rel == ".":
            return False
        ignored = False
        for base, pats in self._stack:
            if not pats:
                continue
            if base and not (rel == base.rstrip("/") or rel.startswith(base)):
                continue
            local = rel[len(base) :] if base else rel
            if not local:
                continue
            # TarIgnore.match expects no leading slash
            for pat in pats:
                if pat.dir_only and not is_dir:
                    if not pat.regex.search(local) and not pat.regex.search(local + "/"):
                        continue
                if pat.regex.search(local) or (
                    is_dir and pat.regex.search(local.rstrip("/") + "/")
                ):
                    ignored = not pat.negate
        return ignored


def load_root_gitignore(root: Path) -> TarIgnore:
    """Convenience: only the project-root ``.gitignore`` as a TarIgnore."""
    path = root / ".gitignore"
    if not path.is_file():
        return TarIgnore()
    try:
        return TarIgnore.from_text(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return TarIgnore()
