# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0002: source.size"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0002"
CODE = 'source.size'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/{src,tests,apps,lib}/**/*']
DEFAULT_SEVERITY = 'ok'
IZEABLE = False
IZE_TARGETS = []
TITLE = "No oversized source files"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
