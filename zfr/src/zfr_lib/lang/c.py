# SPDX-License-Identifier: AGPL-3.0-or-later
"""C template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "c"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.c", "tests/{stem}_test.c", "{stem}.bash", "docs/{stem}.adoc"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.tests", "tests/ present")]
    return [Finding("note", "lang.tests", "no tests/ directory", "tests/",
        fix="Add tests/ and meson test() entries like the C family templates.")]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".c": 2.0},
    wire=WireSpec(kind="c", app_ext="c", test_ext="c"),
    puff_fn=_puff,
    lint_fn=_lint,
)
