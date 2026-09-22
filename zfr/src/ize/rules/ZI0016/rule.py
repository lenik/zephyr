# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0016: ize.i18n.po-nowrap"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0016"
CODE = 'ize.i18n.po-nowrap'
PRIORITY = 160.0
DEPENDENCIES = []
GLOBS = ['/po/**']
TITLE = "Rewrite source .po catalogs without line wrapping"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_po_no_wrap())

