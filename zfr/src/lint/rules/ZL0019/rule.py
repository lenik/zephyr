# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0019: meson.license"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0019"
CODE = 'meson.license'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/meson.build']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0008', 'ZI0011', 'ZI0012']
TITLE = "meson license AGPL-3.0-or-later"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
