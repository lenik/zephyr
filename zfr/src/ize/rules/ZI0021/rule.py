# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0021: ize.c.bas"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0021"
CODE = 'ize.c.bas'
PRIORITY = 145.0
DEPENDENCIES = []
GLOBS = ['/src/', '/meson.build']
TITLE = "C-family bas i18n/logger/LOCALEDIR and gettext spacing"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_c_bas())

