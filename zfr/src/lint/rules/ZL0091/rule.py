# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0091: source.hardcoded.version"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0091"
CODE = 'source.hardcoded.version'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/**/*.{c,cc,cpp,h,py,sh,in,rs,go}', '/meson.build']
DEFAULT_SEVERITY = 'warn'
IZEABLE = True
IZE_TARGETS = ['ZI0014']
TITLE = "Hardcoded project version in sources (use @VERSION@ / PROJECT_VERSION)"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
