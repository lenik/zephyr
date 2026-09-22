# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0023: meson.asciidoctor"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0023"
CODE = 'meson.asciidoctor'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/meson.build']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0011', 'ZI0008']
TITLE = "Meson invokes asciidoctor for man pages"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
