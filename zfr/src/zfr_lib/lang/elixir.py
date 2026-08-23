# SPDX-License-Identifier: AGPL-3.0-or-later
"""Elixir template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "elixir"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.ex", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))


SPEC = LangSpec(
    name=NAME,
    ext_weights={".ex": 4.0, ".exs": 3.0},
    name_weights={"mix.exs": 20.0, "mix.lock": 8.0},
    depends=((re.compile(r"\belixir\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
