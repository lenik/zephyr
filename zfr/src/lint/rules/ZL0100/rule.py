# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0100: ci.release_scripts"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0100"
CODE = 'ci.release_scripts'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/.github/', '/scripts/ci/', '/debian/control', '/packaging/rpm/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0007']
TITLE = "scripts/ci helpers for multi-distro package builds"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
