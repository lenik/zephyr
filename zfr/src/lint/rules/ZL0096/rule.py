# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0096: layout.scripts"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0096"
CODE = 'layout.scripts'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/scripts/', '/meson.build', '/*.sh']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0023']
TITLE = "Build/deploy/maintenance scripts live under scripts/"
DETAIL = """Root-level *.sh helpers and meson run_target bodies for look / install-symlinks / uninstall-symlinks / posync / deploy belong in scripts/. Run `zfr ize` to move and rewire."""


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
