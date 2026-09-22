# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0004: ize.debian.rules"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0004"
CODE = 'ize.debian.rules'
PRIORITY = 40.0
DEPENDENCIES = ['ZI0003']
GLOBS = ['/debian/rules', '/debian/**']
TITLE = "Align debian/rules with Meson dh helper"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_debian_rules())

