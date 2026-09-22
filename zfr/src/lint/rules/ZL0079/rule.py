# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0079: template.coverage"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0079"
CODE = 'template.coverage'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0002']
TITLE = "Language template structural files present"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
