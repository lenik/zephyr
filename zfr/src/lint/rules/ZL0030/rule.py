# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0030: rpm.topdir.leftover"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0030"
CODE = 'rpm.topdir.leftover'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/packaging/rpm/**', '/rpmbuild/**', '/debian/**', '/meson.build']
DEFAULT_SEVERITY = 'warn'
IZEABLE = True
IZE_TARGETS = ['ZI0020']
TITLE = "Project-local rpmbuild/ directory"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
