# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0033: rpm.URL"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0033"
CODE = 'rpm.URL'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/packaging/rpm/', '/rpmbuild/', '/debian/', '/meson.build']
DEFAULT_SEVERITY = 'warn'
IZEABLE = True
IZE_TARGETS = ['ZI0013', 'ZI0020']
TITLE = "RPM spec URL matches debian Homepage"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
