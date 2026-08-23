# SPDX-License-Identifier: AGPL-3.0-or-later
"""OCaml template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "ocaml"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"),
        puff_paths(tmpl, stem, "src/{stem}.ml"),
    )


SPEC = LangSpec(
    name=NAME,
    ext_weights={".ml": 4.0, ".mli": 2.0},
    name_weights={"dune-project": 20.0, "dune": 12.0},
    depends=((re.compile(r"\b(ocaml|ocaml-findlib|ocaml-nox)\b", re.I), 12.0),),
    meson_tokens={"ocamlfind": 16.0},
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
