# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0006: ize.changelog"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0006"
CODE = 'ize.changelog'
PRIORITY = 60.0
DEPENDENCIES = []
GLOBS = ['/debian/changelog', '/VERSION']
TITLE = "Ensure debian/changelog and VERSION file"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_changelog_version())

