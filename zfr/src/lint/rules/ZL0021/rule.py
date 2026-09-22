# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0021: meson.version_source"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0021"
CODE = 'meson.version_source'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/meson.build']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0008', 'ZI0014']
TITLE = "Meson version from zfr version"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
