# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0074: lang.zig.build"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0074"
CODE = 'lang.zig.build'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/']
DEFAULT_SEVERITY = 'error'
IZEABLE = False
IZE_TARGETS = []
TITLE = "Zig build.zig present"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
