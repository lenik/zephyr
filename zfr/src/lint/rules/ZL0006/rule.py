# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0006: layout.VERSION"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0006"
CODE = 'layout.VERSION'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/VERSION', '/debian/changelog', '/.githooks/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0006', 'ZI0007']
TITLE = "VERSION file synced with changelog"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
