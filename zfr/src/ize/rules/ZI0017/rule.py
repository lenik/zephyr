# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0017: ize.commit"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0017"
CODE = 'ize.commit'
PRIORITY = 900.0
DEPENDENCIES = []
GLOBS = ['/']
TITLE = "Bump patch version and git commit (--commit)"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.commit_changes())

