# SPDX-License-Identifier: AGPL-3.0-or-later
"""``.lintignore`` support — gitignore-style patterns in any subdirectory."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path, PurePosixPath

from lint.globmatch import path_matches_glob


def _parse_lintignore(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


@lru_cache(maxsize=64)
def _collect_ignore_rules(root_s: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return ``(dir_rel_with_slash, patterns)`` for every ``.lintignore`` under *root*."""
    root = Path(root_s)
    rules: list[tuple[str, tuple[str, ...]]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip noisy dirs
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".git", "build", "node_modules", "dist", "__pycache__", "rpmbuild"}
            and not d.startswith(".")
        ]
        if ".lintignore" not in filenames:
            continue
        p = Path(dirpath)
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            continue
        base = "" if rel in (".", "") else rel.rstrip("/") + "/"
        patterns = tuple(_parse_lintignore(p / ".lintignore"))
        if patterns:
            rules.append((base, patterns))
    return tuple(rules)


def clear_lintignore_cache() -> None:
    _collect_ignore_rules.cache_clear()


def is_lint_ignored(root: Path, path: Path) -> bool:
    """True if *path* matches a ``.lintignore`` pattern scoped to its directory."""
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            return False
    if not rel or rel == ".":
        return False

    for base, patterns in _collect_ignore_rules(str(root.resolve())):
        if base and not (rel == base.rstrip("/") or rel.startswith(base)):
            continue
        # Path relative to the .lintignore directory
        local = rel[len(base) :] if base else rel
        if not local:
            continue
        for pat in patterns:
            # Leading / in pattern → only from that lintignore dir root
            if pat.startswith("/"):
                if path_matches_glob("/" + local, pat):
                    return True
            else:
                # Match any suffix under this lintignore scope
                if path_matches_glob(local, pat) or path_matches_glob(
                    "/" + local, "/" + pat.lstrip("/")
                ):
                    return True
                # Also allow basename-only patterns like *.css
                if "/" not in pat.rstrip("/") and path_matches_glob(
                    PurePosixPath(local).name, pat
                ):
                    return True
    return False
