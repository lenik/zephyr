# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0015: ize.i18n.derive"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0015"
CODE = 'ize.i18n.derive'
PRIORITY = 170.0
DEPENDENCIES = ['ZI0018']
GLOBS = ['/po/**', '/meson.build']
TITLE = "Meson build+install derived locale catalogs"

def ize(files: list[Path], session: Any = None):
    from ize._bridge import run_step

    if session is None:
        from lint.editlist import EditList
        return EditList()
    return run_step(session, CODE, lambda eng: eng.derive_i18n_locales())

