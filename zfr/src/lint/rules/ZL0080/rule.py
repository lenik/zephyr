# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0080: readme.placeholder.*"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0080"
CODE = 'readme.placeholder.*'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/README*', '/readme*']
DEFAULT_SEVERITY = 'varies'
IZEABLE = False
IZE_TARGETS = []
TITLE = "README still has template placeholder banner"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
