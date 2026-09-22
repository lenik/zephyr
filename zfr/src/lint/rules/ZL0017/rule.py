# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0017: debian.Depends.bash-shlib"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0017"
CODE = 'debian.Depends.bash-shlib'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/debian/**']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0003', 'ZI0004', 'ZI0005', 'ZI0006']
TITLE = "bash package Depends includes bash-shlib"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
