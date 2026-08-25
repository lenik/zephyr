# SPDX-License-Identifier: AGPL-3.0-or-later
"""C++ template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "cpp"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.cpp", "tests/{stem}_test.cpp", "{stem}.bash", "docs/{stem}.adoc"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.tests", _("tests/ present"))]
    return [Finding("note", "lang.tests", _("no tests/ directory"), "tests/",
        fix=_("Add tests/ and meson test() entries like the C family templates."))]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".cpp": 3.0, ".cc": 3.0, ".cxx": 3.0, ".hpp": 2.0, ".hh": 2.0, ".hxx": 2.0, ".h": 0.35},
    wire=WireSpec(kind="c", app_ext="cpp", test_ext="cpp"),
    puff_fn=_puff,
    lint_fn=_lint,
)
