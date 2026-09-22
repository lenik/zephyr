# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0012: ize.completion"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0012"
CODE = 'ize.completion'
PRIORITY = 120.0
DEPENDENCIES = []
GLOBS = ['/']
TITLE = "Add bash-completion stubs for command puffs"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_completion())

