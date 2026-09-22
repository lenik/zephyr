# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0093: i18n.po.placeholder"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0093"
CODE = 'i18n.po.placeholder'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/po/', '/man/', '/meson.build']
DEFAULT_SEVERITY = 'warn'
IZEABLE = False
IZE_TARGETS = []
TITLE = "gettext .po empty msgstr or omitted msgid-copy (keep-English field literals exempt)"
DETAIL = None


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
