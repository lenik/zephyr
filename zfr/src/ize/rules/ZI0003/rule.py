# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0003: ize.debian.control"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0003"
CODE = 'ize.debian.control'
PRIORITY = 30.0
DEPENDENCIES = []
GLOBS = ['/debian/**']
TITLE = "Patch debian/control for zephyr style"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.patch_debian_control())

