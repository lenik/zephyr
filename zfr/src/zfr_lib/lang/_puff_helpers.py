# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared puff path helpers for language modules."""

from __future__ import annotations

from pathlib import Path

from .. import TEMPLATE_PUFF, iter_files


def puff_paths(tmpl: Path, stem: str, *rels: str) -> list[Path]:
    out: list[Path] = []
    for rel in rels:
        p = tmpl.joinpath(*rel.format(stem=stem).split("/"))
        if p.exists():
            out.append(p)
    return out


def puff_dir_if_exists(tmpl: Path, rel: str) -> list[Path]:
    p = tmpl / rel
    return [p] if p.is_dir() else []


def puff_generic(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    found: list[Path] = []
    for path in iter_files(tmpl):
        if stem in path.name or pascal in path.name:
            found.append(path)
    return found


def merge_puff(*groups: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for group in groups:
        for p in group:
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                out.append(p)
    return out
