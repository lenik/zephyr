# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0076: lang.go.mod"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0076"
CODE = 'lang.go.mod'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/']
DEFAULT_SEVERITY = 'error'
IZEABLE = False
IZE_TARGETS = []
TITLE = "Go go.mod present"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
