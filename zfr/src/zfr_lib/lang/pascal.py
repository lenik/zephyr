# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pascal (Free Pascal) template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "pascal"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(
            tmpl,
            stem,
            "src/{stem}.pas",
            "src/commons.pas",
            "tests/test_commons.pas",
            "{stem}.bash",
            "docs/{stem}.adoc",
        )
    )


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.pascal.tests", "tests/ present")]
    return [
        Finding(
            "warn",
            "lang.pascal.tests",
            "no tests/ (pascal template uses fpc + meson test)",
            "tests/",
            fix="Add tests/test_commons.pas and meson test() with fpc.",
        )
    ]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".pas": 4.0, ".pp": 3.0, ".dpr": 3.0, ".inc": 1.5},
    name_weights={"fpc.cfg": 12.0},
    depends=((re.compile(r"\bfpc\b|\bfpc-\w+\b", re.I), 12.0),),
    meson_hints=(("find_program('fpc'", 16.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
)
