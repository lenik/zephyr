# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0101: ci.matrix_arch"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0101"
CODE = 'ci.matrix_arch'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/.github/**', '/scripts/ci/**', '/debian/control', '/packaging/rpm/**']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0007']
TITLE = "CI matrix arch policy (debian armhf/v7; raspi armhf/v6; uos/kylin loong64)"
DETAIL = """Debian armhf uses linux/arm/v7; raspi_* uses linux/arm/v6. loong64 only for uos_*/kylin_*. Ubuntu may add i386/amd64v3; also mingw/cygwin matrix sections for Windows native builds."""


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
