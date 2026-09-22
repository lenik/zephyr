# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0010: ize.man.stub"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0010"
CODE = 'ize.man.stub'
PRIORITY = 100.0
DEPENDENCIES = []
GLOBS = ['/man/**']
TITLE = "Create AsciiDoc man page stubs"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_man_stubs())

