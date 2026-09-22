# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0001: source.long"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0001"
CODE = 'source.long'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/{src,tests,apps,lib}/**/*.{c,cc,cpp,cxx,h,hpp,py,rs,go,sh,in}']
DEFAULT_SEVERITY = 'varies'
IZEABLE = False
IZE_TARGETS = []
TITLE = "Source file length; extract to package subdirectory"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
