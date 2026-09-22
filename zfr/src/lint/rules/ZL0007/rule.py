# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0007: layout.pre-commit"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0007"
CODE = 'layout.pre-commit'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/.githooks/**', '/.git/hooks/**']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0006', 'ZI0007']
TITLE = "Git pre-commit hook syncs VERSION"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
