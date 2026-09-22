# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0103: rpm.patches"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0103"
CODE = 'rpm.patches'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/packaging/rpm/**', '/rpmbuild/**', '/debian/**', '/meson.build']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0013', 'ZI0020']
TITLE = "packaging/rpm/*.patch wired as PatchN + %autosetup/%patch"
DETAIL = """RPM-only patches under packaging/rpm/*.patch must be listed as PatchN: in the spec and applied in %prep (%autosetup -p1 or %patch -PN -p1). Makefile and build-rpm.sh copy them into SOURCES."""


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
