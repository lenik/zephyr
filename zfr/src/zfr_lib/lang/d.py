# SPDX-License-Identifier: AGPL-3.0-or-later
"""D template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "d"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(
            tmpl,
            stem,
            "src/{stem}.d",
            "src/commons.d",
            "tests/test_commons.d",
            "{stem}.bash",
            "docs/{stem}.adoc",
        )
    )


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.d.tests", _("tests/ present"))]
    return [
        Finding(
            "warn",
            "lang.d.tests",
            _("no tests/ (D template uses ldc/dmd + meson test)"),
            "tests/",
            fix=_("Add tests/test_commons.d and meson test() executable."),
        )
    ]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".d": 4.0, ".di": 2.0},
    name_weights={"dub.json": 15.0, "dub.sdl": 12.0},
    depends=((re.compile(r"\b(ldc|dmd|gdc|dlang)\b", re.I), 12.0),),
    meson_tokens={"d": 18.0},
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
)
