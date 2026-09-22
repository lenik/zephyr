# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0052: i18n.linguas"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0052"
CODE = 'i18n.linguas'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/po/', '/man/', '/meson.build']
DEFAULT_SEVERITY = 'warn'
IZEABLE = True
IZE_TARGETS = ['ZI0018', 'ZI0015', 'ZI0016']
TITLE = "po/LINGUAS present when po/ exists"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
