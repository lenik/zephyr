# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0013: ize.rpm"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0013"
CODE = 'ize.rpm'
PRIORITY = 130.0
DEPENDENCIES = []
GLOBS = ['/packaging/rpm/', '/debian/', '/meson.build']
TITLE = "Align packaging/rpm/Makefile and RPM spec with debian/Meson"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_rpm())

