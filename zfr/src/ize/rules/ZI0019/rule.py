# SPDX-License-Identifier: AGPL-3.0-or-later
"""ZI0019: ize.i18n.man-locale"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ID = "ZI0019"
CODE = 'ize.i18n.man-locale'
PRIORITY = 155.0
DEPENDENCIES = []
GLOBS = ['/man/**']
TITLE = "Do not scaffold man/<locale>/*.adoc (missing man translations are lint-only)"

def ize(files: list[Path], session: Any = None):
    from lint.editlist import EditList

    return EditList()

