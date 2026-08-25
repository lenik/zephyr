# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fortran template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "fortran"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(
            tmpl,
            stem,
            "src/{stem}.f90",
            "src/commons.f90",
            "tests/test_commons.f90",
            "{stem}.bash",
            "docs/{stem}.adoc",
        )
    )


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.fortran.tests", _("tests/ present"))]
    return [
        Finding(
            "warn",
            "lang.fortran.tests",
            _("no tests/ (fortran template uses gfortran + meson test)"),
            "tests/",
            fix=_("Add tests/test_commons.f90 and meson test() executable."),
        )
    ]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".f90": 4.0, ".f03": 4.0, ".f": 2.0, ".for": 2.0, ".f95": 3.5},
    depends=((re.compile(r"\bgfortran\b|\bfortran-\w+\b", re.I), 12.0),),
    meson_tokens={"fortran": 18.0},
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
)
