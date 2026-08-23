# SPDX-License-Identifier: AGPL-3.0-or-later
"""C# template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "csharp"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_dir_if_exists(tmpl, f"apps/{stem}"), puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".cs": 4.0},
    depends=((re.compile(r"\bdotnet(?:-sdk)?\b", re.I), 12.0),),
    wire=WireSpec(kind="csharp"),
    puff_fn=_puff,
)
