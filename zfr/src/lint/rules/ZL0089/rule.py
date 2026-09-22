# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0089: i18n.po.quality"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0089"
CODE = 'i18n.po.quality'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/po/', '/man/', '/meson.build']
DEFAULT_SEVERITY = 'varies'
IZEABLE = False
IZE_TARGETS = []
TITLE = "gettext .po completion (msgid-copy counts as untranslated; ≤20% ≈ missing)"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
