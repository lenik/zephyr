# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0040: rpm.noarch.elf"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0040"
CODE = 'rpm.noarch.elf'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/packaging/rpm/**', '/rpmbuild/**', '/debian/**', '/meson.build']
DEFAULT_SEVERITY = 'error'
IZEABLE = True
IZE_TARGETS = ['ZI0013', 'ZI0020']
TITLE = "noarch RPM with Meson executable()"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
