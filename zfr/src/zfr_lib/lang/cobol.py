# SPDX-License-Identifier: AGPL-3.0-or-later
"""COBOL (GnuCOBOL) template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "cobol"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(
            tmpl,
            stem,
            "src/{stem}.cob",
            "src/commons.cob",
            "tests/test_commons.sh",
            "{stem}.bash",
            "docs/{stem}.adoc",
        )
    )


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.cobol.tests", _("tests/ present"))]
    return [
        Finding(
            "warn",
            "lang.cobol.tests",
            _("no tests/ (cobol template uses cobc + meson test)"),
            "tests/",
            fix=_("Add tests/test_commons.sh or similar smoke test for cobc."),
        )
    ]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".cob": 4.0, ".cbl": 4.0, ".cpy": 2.0},
    depends=((re.compile(r"\bcobc\b|\bgcobol\b|\bgnucobol\b", re.I), 12.0),),
    meson_hints=(("find_program('cobc'", 16.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
)
