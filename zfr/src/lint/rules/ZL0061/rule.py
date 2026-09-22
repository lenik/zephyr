# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0061: identity.rpm.Name"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0061"
CODE = 'identity.rpm.Name'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/debian/control', '/meson.build', '/packaging/rpm/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0013']
TITLE = "RPM spec Name matches package name"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
