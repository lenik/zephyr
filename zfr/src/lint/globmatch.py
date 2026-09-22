# SPDX-License-Identifier: AGPL-3.0-or-later
"""File globs for lint/ize rule selection.

Patterns starting with ``/`` match from the project root (pathname is always
normalized with a leading ``/``). Patterns without ``/`` match any path suffix
(from an arbitrary directory). Supports ``*``, ``?``, ``[]``, ``{a,b}``, ``**``.
"""

from __future__ import annotations

import re
from functools import lru_cache


def normalize_pathname(rel: str) -> str:
    """Project-relative path with a leading ``/`` (dirs may end with ``/``)."""
    s = rel.replace("\\", "/").strip()
    if not s or s == ".":
        return "/"
    if not s.startswith("/"):
        s = "/" + s
    # collapse duplicate slashes except keep single leading
    while "//" in s:
        s = s.replace("//", "/")
    return s


def _expand_braces(pattern: str) -> list[str]:
    """Expand one level of ``{a,b,c}`` (recursive)."""
    m = re.search(r"\{([^{}]*)\}", pattern)
    if not m:
        return [pattern]
    pre, post = pattern[: m.start()], pattern[m.end() :]
    alts = m.group(1).split(",")
    out: list[str] = []
    for alt in alts:
        out.extend(_expand_braces(pre + alt + post))
    return out


def _glob_to_regex(pattern: str, *, anchored: bool) -> re.Pattern[str]:
    """Convert a single brace-expanded glob to a regex."""
    i = 0
    parts: list[str] = []
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*" and i + 1 < n and pattern[i + 1] == "*":
            # ** — match across path segments
            if i + 2 < n and pattern[i + 2] == "/":
                parts.append("(?:.*/)?")
                i += 3
            else:
                parts.append(".*")
                i += 2
            continue
        if c == "*":
            parts.append("[^/]*")
            i += 1
            continue
        if c == "?":
            parts.append("[^/]")
            i += 1
            continue
        if c == "[":
            j = i + 1
            if j < n and pattern[j] in ("!", "^"):
                j += 1
            while j < n and pattern[j] != "]":
                j += 1
            if j >= n:
                parts.append(re.escape(c))
                i += 1
                continue
            parts.append(pattern[i : j + 1])
            i = j + 1
            continue
        parts.append(re.escape(c))
        i += 1
    body = "".join(parts)
    if anchored:
        return re.compile("^" + body + "$")
    # unanchored: pattern may match any suffix after a /
    return re.compile("(?:^|/)" + body + "$")


@lru_cache(maxsize=512)
def _compiled_patterns(pattern: str) -> tuple[tuple[bool, re.Pattern[str]], ...]:
    anchored = pattern.startswith("/")
    pats = _expand_braces(pattern)
    out: list[tuple[bool, re.Pattern[str]]] = []
    for p in pats:
        # strip leading / for the regex body when anchored — pathname keeps /
        if p.startswith("/"):
            body = p  # keep leading / in regex so it matches normalize_pathname
            out.append((True, _glob_to_regex(body, anchored=True)))
        else:
            out.append((False, _glob_to_regex(p, anchored=False)))
    return tuple(out)


def path_matches_glob(pathname: str, pattern: str) -> bool:
    """Return True if *pathname* (project-relative) matches *pattern*."""
    path = normalize_pathname(pathname)
    # also try without trailing slash for dirs
    candidates = {path}
    if path != "/" and path.endswith("/"):
        candidates.add(path.rstrip("/"))
    elif path != "/":
        candidates.add(path + "/")
    for anchored, rx in _compiled_patterns(pattern):
        for cand in candidates:
            if anchored:
                if rx.match(cand):
                    return True
            else:
                # match against path without leading / as well as full
                bare = cand[1:] if cand.startswith("/") else cand
                if rx.search(cand) or rx.search(bare) or rx.search("/" + bare):
                    return True
                # suffix match: any directory prefix
                parts = bare.strip("/").split("/")
                for i in range(len(parts)):
                    suffix = "/".join(parts[i:])
                    if rx.search(suffix) or rx.search("/" + suffix):
                        return True
    return False


def path_matches_any(pathname: str, patterns: list[str] | tuple[str, ...]) -> bool:
    if not patterns:
        return False
    return any(path_matches_glob(pathname, p) for p in patterns)
