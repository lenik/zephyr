# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0022: ize.posync"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0022"
CODE = 'ize.posync'
PRIORITY = 180.0
DEPENDENCIES = ['ZI0008']
GLOBS = ['/meson.build', '/scripts/**', '/po/**']
TITLE = "Externalize posync run_target to scripts/posync.sh"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step
    from ize.engine.scripts import ensure_scripts_externalized

    if session is None:
        from lint.editlist import EditList
        return EditList()
    if not (session.root / "po").is_dir():
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: ensure_scripts_externalized(eng, targets=("posync",)))

