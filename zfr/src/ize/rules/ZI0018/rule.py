# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0018: ize.i18n.coverage"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0018"
CODE = 'ize.i18n.coverage'
PRIORITY = 150.0
DEPENDENCIES = []
GLOBS = ['/po/']
TITLE = "Ensure LINGUAS + .po for lint l10n level"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.ensure_i18n_coverage())

