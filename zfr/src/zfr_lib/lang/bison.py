# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bison/Flex parser template language."""
from __future__ import annotations

from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "bison"


def _score_bison(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    src = root / "src"
    if src.is_dir() and list(src.glob("*.y")):
        scores["bison"] += 22.0
        scores["c"] *= 0.2


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(
            tmpl,
            stem,
            "src/{stem}.l",
            "src/{stem}.y",
            "src/{stem}_main.c",
            "{stem}.bash",
            "docs/{stem}.adoc",
        )
    )


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.tests", _("tests/ present"))]
    return [
        Finding(
            "note",
            "lang.tests",
            _("no tests/ directory"),
            "tests/",
            fix=_("Add tests/ with fixture checks for parser dump/format output."),
        )
    ]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".y": 8.0, ".l": 6.0},
    name_weights={"some_puff1.y": 4.0},
    meson_hints=(("find_program('bison'", 16.0), ("find_program('flex'", 14.0)),
    wire=WireSpec(kind="c", app_ext="c", test_ext="c"),
    puff_fn=_puff,
    lint_fn=_lint,
    score_fn=_score_bison,
)
