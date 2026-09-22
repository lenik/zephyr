# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0020: ize.rpm.leftover"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0020"
CODE = 'ize.rpm.leftover'
PRIORITY = 135.0
DEPENDENCIES = []
GLOBS = ['/rpmbuild/**', '/']
TITLE = "Remove project-local rpmbuild/ leftover tree"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.remove_local_rpmbuild())

