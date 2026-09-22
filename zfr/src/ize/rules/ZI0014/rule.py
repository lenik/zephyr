# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0014: ize.subst"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0014"
CODE = 'ize.subst'
PRIORITY = 140.0
DEPENDENCIES = ['ZI0008']
GLOBS = ['/meson.build', '/src/', '/apps/']
TITLE = "Replace hardcoded versions/paths with @VERSION@/@PREFIX@ / config.h"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.subst_versions())

