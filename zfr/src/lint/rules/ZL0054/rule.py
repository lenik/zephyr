# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0054: i18n.po.files"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0054"
CODE = 'i18n.po.files'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/po/', '/man/', '/meson.build']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0018', 'ZI0015', 'ZI0016']
TITLE = "LINGUAS entries have matching .po files"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
