# SPDX-License-Identifier: AGPL-3.0-or-later
"""Haskell template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "haskell"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"), puff_paths(tmpl, stem, "src/Main.hs"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".hs": 4.0, ".lhs": 3.0},
    name_weights={"stack.yaml": 20.0, "cabal.project": 15.0},
    depends=((re.compile(r"\b(ghc|haskell-devscripts)\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
