# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0088: lang.c.bas.gettext_space"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0088"
CODE = 'lang.c.bas.gettext_space'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/']
DEFAULT_SEVERITY = 'warn'
IZEABLE = True
IZE_TARGETS = ['ZI0021']
TITLE = "gettext _() strings must not have leading/trailing spaces"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
