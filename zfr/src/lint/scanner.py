# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project scan: file→rules, reverse merge to rule→files, priority/dep sort.

Walk rules:
  1. Honour ``.gitignore`` (nested) — ignored paths are never visited.
  2. Skip hard-coded noise dirs (``SKIP_DIR_NAMES``) and most dot-dirs.
  3. Prune: if no rule glob can match a directory or anything under it, do
     not traverse into that directory.
  4. Directory-scoped rules match the directory path only (e.g. ``/po/``);
     they do not need every file under that tree.
"""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from lib import SKIP_DIR_NAMES
from lint.base import RuleSpec
from lint.gitignores import GitIgnoreStack
from lint.globmatch import (
    normalize_pathname,
    path_matches_any,
    rules_can_match_under,
)

# Dot-directories that rules may intentionally target.
_DOT_KEEP = frozenset({".githooks", ".github", ".config"})


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


def _should_skip_dirname(name: str) -> bool:
    if name in SKIP_DIR_NAMES:
        return True
    if name.startswith(".") and name not in _DOT_KEEP:
        return True
    return False


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


def iter_scan_paths(
    root: Path,
    rules: list[RuleSpec],
    *,
    honour_gitignore: bool = True,
) -> list[Path]:
    """Return root + reachable dirs/files that are not ignored and not pruned."""
    root = root.resolve()
    out: list[Path] = [root]
    gi = GitIgnoreStack(root) if honour_gitignore else None

    def visit_dir(abs_dir: Path, rel: str) -> None:
        """List *abs_dir*; append children; recurse into kept subdirs."""
        try:
            names = sorted(os.listdir(abs_dir))
        except OSError:
            return
        subdirs: list[tuple[Path, str]] = []
        for name in names:
            child = abs_dir / name
            child_rel = f"{rel}/{name}" if rel else name
            try:
                is_dir = child.is_dir() and not child.is_symlink()
            except OSError:
                continue
            if gi is not None and gi.ignored(child_rel, is_dir=is_dir):
                continue
            if is_dir:
                if _should_skip_dirname(name):
                    continue
                dir_pn = normalize_pathname(child_rel + "/")
                if not rules_can_match_under(dir_pn, rules):
                    continue
                out.append(child)
                subdirs.append((child, child_rel))
            else:
                try:
                    if child.is_file() or child.is_symlink():
                        out.append(child)
                except OSError:
                    continue
        for child, child_rel in subdirs:
            if gi is not None:
                gi.enter(child, child_rel)
            visit_dir(child, child_rel)
            if gi is not None:
                gi.leave()

    visit_dir(root, "")
    return out


def iter_paths(root: Path) -> list[Path]:
    """List paths with gitignore + noise skips, without rule-based pruning."""

    class _All:
        globs = ["/**/*"]

        def matches(self, pathname: str, session: Any = None) -> bool:
            return True

    return iter_scan_paths(root, [_All()])  # type: ignore[list-item]


def scan_project(
    root: Path,
    rules: list[RuleSpec],
    session: Any = None,
) -> tuple[dict[str, list[RuleSpec]], dict[str, list[Path]]]:
    """Return ``(file→rules, rule→files)`` for *root*."""
    file_to_rules: dict[str, list[RuleSpec]] = {}
    rule_to_files: dict[str, list[Path]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)

    for path in iter_scan_paths(root, rules):
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

    for rule in rules:
        rule_to_files.setdefault(rule.id, [])

    return file_to_rules, dict(rule_to_files)


def sort_rules(rules: list[RuleSpec]) -> list[RuleSpec]:
    """Topological sort by DEPENDENCIES, then PRIORITY ascending, then id."""
    by_id = {r.id: r for r in rules}
    deps: dict[str, set[str]] = {
        r.id: {d for d in r.dependencies if d in by_id} for r in rules
    }
    remaining = set(by_id)
    ordered: list[RuleSpec] = []
    while remaining:
        ready = [rid for rid in remaining if not (deps[rid] & remaining)]
        if not ready:
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
