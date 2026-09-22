# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0092: source.hardcoded"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0092"
CODE = 'source.hardcoded'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/**/*.{c,cc,cpp,h,py,sh,in,rs,go}', '/meson.build']
DEFAULT_SEVERITY = 'ok'
IZEABLE = False
IZE_TARGETS = []
TITLE = "No hardcoded install paths or project version strings"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
