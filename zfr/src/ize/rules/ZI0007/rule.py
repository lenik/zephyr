# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0007: ize.stdfiles"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0007"
CODE = 'ize.stdfiles'
PRIORITY = 70.0
DEPENDENCIES = []
GLOBS = ['/']
TITLE = "Refresh LICENSE, .githooks, .cursor/rules from shipped zfr copies"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_std_files())

