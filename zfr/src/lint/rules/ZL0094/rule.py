# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0094: meson.version_subst"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0094"
CODE = 'meson.version_subst'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/meson.build']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0008', 'ZI0014']
TITLE = "Project version substituted by Meson config and used in at least one source"
DETAIL = """meson.build should feed VERSION/PROJECT_VERSION via configuration_data (ize_cfg / config_h / paths_cfg), and at least one source under src/ (or a configure_file input) must consume @VERSION@ or PROJECT_VERSION."""


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
