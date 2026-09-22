# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0004: layout.man"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0004"
CODE = 'layout.man'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/man/', '/docs/man/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0009', 'ZI0010', 'ZI0011']
TITLE = "AsciiDoc man page sources under man/"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
