# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZL0095: layout.posync"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZL0095"
CODE = 'layout.posync'
PRIORITY = 100.0
DEPENDENCIES: list[str] = []
GLOBS = ['/meson.build', '/scripts/', '/po/']
DEFAULT_SEVERITY = 'varies'
IZEABLE = True
IZE_TARGETS = ['ZI0022']
TITLE = "posync run_target is externalized as scripts/posync.sh"
DETAIL = """When po/ exists, meson.run_target('posync') must call scripts/posync.sh rather than an inline bash -euc heredoc. Run `zfr ize` to extract."""


def matches(pathname: str, session: Any = None) -> bool:
    return True


def lint(files: list[Path], session: Any = None) -> list:
    from lint._collect import filter_findings

    if session is None:
        return []
    return filter_findings(session, CODE)
