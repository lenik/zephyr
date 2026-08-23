# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ruby template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "ruby"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.rb", "src/commons.rb", "{stem}.bash", "docs/{stem}.adoc"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".rb": 4.0},
    name_weights={"gemfile": 20.0, "rakefile": 8.0},
    shebangs=((re.compile(r"^#!.*\bruby\b"), 4.0),),
    depends=((re.compile(r"\bruby\b", re.I), 8.0),),
    wire=WireSpec(kind="script", app_list="app_scripts", script_ext="rb"),
    puff_fn=_puff,
)
