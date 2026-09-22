# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0015: debian.source.format"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0015"
CODE = 'debian.source.format'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/debian/**']
DEFAULT_SEVERITY = 'ok'
IZEABLE = True
IZE_TARGETS = ['ZI0003', 'ZI0004', 'ZI0005', 'ZI0006']
TITLE = "debian/source/format native 3.0"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
