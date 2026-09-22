# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0086: lang.c.bas.logger"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0086"
CODE = 'lang.c.bas.logger'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0021']
TITLE = "C-family sources define_logger() via bas/log/deflog.h"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
