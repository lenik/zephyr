# SPDX-License-Identifier: AGPL-3.0-or-later
"""Erlang template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "erlang"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.erl", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".erl": 4.0, ".hrl": 2.0},
    name_weights={"mix.exs": 8.0, "rebar.config": 20.0},
    depends=((re.compile(r"\berlang\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
