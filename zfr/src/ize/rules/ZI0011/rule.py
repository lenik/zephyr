# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0011: ize.meson.man"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0011"
CODE = 'ize.meson.man'
PRIORITY = 110.0
DEPENDENCIES = ['ZI0008']
GLOBS = ['/meson.build', '/man/']
TITLE = "Add Meson asciidoctor man page targets"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.patch_meson_man_targets())

