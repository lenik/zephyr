# SPDX-License-Identifier: AGPL-3.0-or-later
"""Swift template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "swift"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"), puff_paths(tmpl, stem, "src/main.swift"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".swift": 4.0},
    name_weights={"package.swift": 25.0},
    depends=((re.compile(r"\bswift(?:lang)?\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
