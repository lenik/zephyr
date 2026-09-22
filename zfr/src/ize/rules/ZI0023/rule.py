# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0023: ize.scripts"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0023"
CODE = 'ize.scripts'
PRIORITY = 190.0
DEPENDENCIES = ['ZI0008']
GLOBS = ['/meson.build', '/scripts/**']
TITLE = "Move build/deploy/maintenance scripts under scripts/"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step
    from ize.engine.scripts import ensure_scripts_externalized

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(
        session,
        CODE,
        lambda eng: ensure_scripts_externalized(
            eng, targets=("look", "install-symlinks", "uninstall-symlinks", "deploy")
        ),
    )

