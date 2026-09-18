# SPDX-License-Identifier: AGPL-3.0-or-later
"""Load the ``zfr lint --browse`` shell from resource files."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from string import Template

_TITLE = "zfr lint"
_ASSETS = Path(__file__).resolve().parent / "browse_assets"


@lru_cache(maxsize=1)
def _shell_html() -> str:
    """Return the browse SPA HTML (CSS/JS inlined from ``lint/browse_assets/``)."""
    html = (_ASSETS / "shell.html").read_text(encoding="utf-8")
    css = (_ASSETS / "browse.css").read_text(encoding="utf-8")
    js = (_ASSETS / "browse.js").read_text(encoding="utf-8")
    return Template(html).substitute(title=_TITLE, css=css, js=js)
