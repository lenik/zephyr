# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0001: ize.mesonize"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0001"
CODE = 'ize.mesonize'
PRIORITY = 10.0
DEPENDENCIES = []
GLOBS = ['/']
TITLE = "Convert Autotools/CMake with 2meson"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.mesonize())

