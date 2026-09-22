# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0099: ci.release_workflow"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0099"
CODE = 'ci.release_workflow'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/.github/**', '/scripts/ci/**', '/debian/control', '/packaging/rpm/**']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0007']
TITLE = "GitHub Actions release-packages workflow (Docker matrix, no nested deps)"
DETAIL = """Expect .github/workflows/release-packages.yml triggered on release published, plus scripts/ci helpers. Peer deps use scripts/ci/deps.conf and install-only fetch (never nested-build). Apt component is main."""


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
