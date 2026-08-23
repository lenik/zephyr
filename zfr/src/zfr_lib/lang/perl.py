# SPDX-License-Identifier: AGPL-3.0-or-later
"""Perl template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "perl"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.pl", "{stem}.bash", "docs/{stem}.adoc"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".pl": 4.0, ".pm": 3.5, ".t": 2.0},
    name_weights={"makefile.pl": 12.0, "cpanfile": 12.0},
    shebangs=((re.compile(r"^#!.*\bperl\b"), 4.0),),
    depends=((re.compile(r"\bperl\b", re.I), 8.0),),
    wire=WireSpec(kind="script", app_list="app_scripts", script_ext="pl"),
    puff_fn=_puff,
)
