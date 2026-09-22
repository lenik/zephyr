# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project scan: file→rules, reverse merge to rule→files, priority/dep sort."""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from lib import SKIP_DIR_NAMES
from lint.base import RuleSpec
from lint.globmatch import normalize_pathname, path_matches_any


def iter_paths(root: Path) -> list[Path]:
    """Files and directories under *root* (skip build/VCS noise), plus project root."""
    out: list[Path] = [root]
    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")
        ]
        if p != root:
            out.append(p)
        for fn in filenames:
            out.append(p / fn)
    return out


def _rel_pathname(root: Path, path: Path) -> str:
    if path == root:
        return "/"
    try:
        rel = path.relative_to(root)
    except ValueError:
        return normalize_pathname(str(path))
    s = str(rel).replace("\\", "/")
    if path.is_dir():
        return normalize_pathname(s + "/")
    return normalize_pathname(s)


def match_rules_for_path(
    pathname: str,
    rules: list[RuleSpec],
    session: Any = None,
) -> list[RuleSpec]:
    hit: list[RuleSpec] = []
    for rule in rules:
        if not path_matches_any(pathname, rule.globs):
            continue
        if not rule.matches(pathname, session):
            continue
        hit.append(rule)
    return hit


def scan_project(
    root: Path,
    rules: list[RuleSpec],
    session: Any = None,
) -> tuple[dict[str, list[RuleSpec]], dict[str, list[Path]]]:
    """Return ``(file→rules, rule→files)`` for *root*."""
    file_to_rules: dict[str, list[RuleSpec]] = {}
    rule_to_files: dict[str, list[Path]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)

    for path in iter_paths(root):
        pathname = _rel_pathname(root, path)
        matched = match_rules_for_path(pathname, rules, session)
        if not matched:
            continue
        file_to_rules[pathname] = matched
        for rule in matched:
            key = str(path.resolve()) if path.exists() else pathname
            if key in seen[rule.id]:
                continue
            seen[rule.id].add(key)
            rule_to_files[rule.id].append(path)

    # Ensure every rule key exists (even if empty — caller may skip)
    for rule in rules:
        rule_to_files.setdefault(rule.id, [])

    return file_to_rules, dict(rule_to_files)


def sort_rules(rules: list[RuleSpec]) -> list[RuleSpec]:
    """Topological sort by DEPENDENCIES, then PRIORITY ascending, then id."""
    by_id = {r.id: r for r in rules}
    # Only keep deps that are in the selected set
    deps: dict[str, set[str]] = {
        r.id: {d for d in r.dependencies if d in by_id} for r in rules
    }
    remaining = set(by_id)
    ordered: list[RuleSpec] = []
    while remaining:
        ready = [
            rid
            for rid in remaining
            if not (deps[rid] & remaining)
        ]
        if not ready:
            # cycle — break by priority
            ready = list(remaining)
        ready.sort(key=lambda rid: (by_id[rid].priority, rid))
        pick = ready[0]
        remaining.remove(pick)
        ordered.append(by_id[pick])
    return ordered


def select_scheduled(
    rules: list[RuleSpec],
    rule_to_files: dict[str, list[Path]],
    *,
    require_files: bool = True,
) -> list[tuple[RuleSpec, list[Path]]]:
    """Rules that matched at least one path (unless require_files=False), sorted."""
    selected = []
    for r in rules:
        files = rule_to_files.get(r.id, [])
        if require_files and not files:
            continue
        selected.append(r)
    ordered = sort_rules(selected)
    return [(r, rule_to_files.get(r.id, [])) for r in ordered]
