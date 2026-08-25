# SPDX-License-Identifier: AGPL-3.0-or-later
"""Nim template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "nim"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(tmpl, stem, "src/{stem}.nim", "tests/test_commons.nim", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot")
    )


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.nim.tests", _("tests/ present"))]
    return [Finding("warn", "lang.nim.tests", _("no tests/ (nim template uses unittest + meson test)"), "tests/",
        fix=_("Add tests/test_*.nim and meson test() with nim r."))]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".nim": 4.0, ".nims": 2.0},
    name_weights={"nim.cfg": 12.0, "nimble": 15.0},
    depends=((re.compile(r"\bnim\b", re.I), 12.0),),
    meson_tokens={"nim": 18.0},
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
)
