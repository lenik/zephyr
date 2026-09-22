# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0083: layout.gitignore*"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0083"
CODE = 'layout.gitignore*'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/.gitignore']
DEFAULT_SEVERITY = 'varies'
IZEABLE = False
IZE_TARGETS = []
TITLE = "Root and component .gitignore coverage (node_modules/, dist/, backend/src/generated/, …)"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
