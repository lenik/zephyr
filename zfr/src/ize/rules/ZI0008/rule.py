# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0008: ize.meson.patch"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0008"
CODE = 'ize.meson.patch'
PRIORITY = 80.0
DEPENDENCIES = []
GLOBS = ['/meson.build', '/**/meson.build']
TITLE = "Patch meson.build (version, license, docs, completion)"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.patch_meson())

