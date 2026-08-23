# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared Debian/Meson field parsers used by lint, dist, about, and ize."""

from __future__ import annotations

import re
from pathlib import Path


def parse_control_stanzas(text: str) -> list[dict[str, str]]:
    stanzas: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    key: str | None = None
    for line in text.splitlines():
        if not line.strip():
            if cur:
                stanzas.append(cur)
                cur = {}
                key = None
            continue
        if key and (line.startswith(" ") or line.startswith("\t")):
            cur[key] += "\n" + line.strip()
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            cur[key] = val.strip()
    if cur:
        stanzas.append(cur)
    return stanzas


def meson_project_fields(root: Path) -> dict[str, str]:
    meson = root / "meson.build"
    out: dict[str, str] = {}
    if not meson.is_file():
        return out
    text = meson.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"project\s*\(\s*['\"]([^'\"]+)['\"]", text)
    if m:
        out["name"] = m.group(1)
    m = re.search(r"license\s*:\s*['\"]([^'\"]+)['\"]", text)
    if m:
        out["license"] = m.group(1)
    return out


# Names used throughout the existing call sites (both spellings).
_parse_control_stanzas = parse_control_stanzas
_parse_control_stanzas = parse_control_stanzas
_meson_project_fields = meson_project_fields
_meson_project_fields = meson_project_fields
