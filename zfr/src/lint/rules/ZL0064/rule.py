# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0064: lang.bash.src"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0064"
CODE = 'lang.bash.src'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = False
IZE_TARGETS = []
TITLE = "Bash src/*.in scripts"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
