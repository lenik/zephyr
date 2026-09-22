# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0002: ize.scaffold"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0002"
CODE = 'ize.scaffold'
PRIORITY = 20.0
DEPENDENCIES = []
GLOBS = ['/']
TITLE = "Add missing language-template scaffold files"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.add_missing_files())

