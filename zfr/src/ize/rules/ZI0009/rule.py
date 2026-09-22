# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0009: ize.man.convert"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0009"
CODE = 'ize.man.convert'
PRIORITY = 90.0
DEPENDENCIES = []
GLOBS = ['/man/', '/docs/']
TITLE = "Convert groff man pages to man/*.adoc"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.convert_manpages())

