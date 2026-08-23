# SPDX-License-Identifier: AGPL-3.0-or-later
"""GNU Smalltalk template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "smalltalk"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.st", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".st": 4.0},
    depends=((re.compile(r"\bgnu-smalltalk\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
