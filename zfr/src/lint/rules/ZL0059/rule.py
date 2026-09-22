# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0059: identity.source_vs_meson"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0059"
CODE = 'identity.source_vs_meson'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/debian/control', '/meson.build', '/packaging/rpm/**']
DEFAULT_SEVERITY = 'warn'
IZEABLE = False
IZE_TARGETS = []
TITLE = "debian Source matches meson project name"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
