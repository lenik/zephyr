# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0102: ci.rpm_deb_deps"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0102"
CODE = 'ci.rpm_deb_deps'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/.github/', '/scripts/ci/', '/debian/control', '/packaging/rpm/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0007']
TITLE = "RPM CI maps Debian Build-Depends; RPM-only patches via %patch"
DETAIL = """When translating debian/control Build-Depends into rpmbuild, apply experiential mappings: bash-builtins → bash (ships bash.pc). RPM-only source tweaks live in packaging/rpm/*.patch and are applied with PatchN + %autosetup/%patch (build-rpm copies them to SOURCES); do not mutate system .pc files in the container."""


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
