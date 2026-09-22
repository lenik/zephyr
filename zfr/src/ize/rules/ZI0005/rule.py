# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0005: ize.debian.docs"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0005"
CODE = 'ize.debian.docs'
PRIORITY = 50.0
DEPENDENCIES = []
GLOBS = ['/debian/**', '/man/**']
TITLE = "Sync debian/docs with installed mans"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.fix_debian_docs())

