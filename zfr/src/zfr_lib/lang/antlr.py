# SPDX-License-Identifier: AGPL-3.0-or-later
"""ANTLR4 parser template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "antlr"


def _score_antlr(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    src = root / "src"
    if src.is_dir() and list(src.glob("*.g4")):
        scores["antlr"] += 22.0
        scores["java"] *= 0.35


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(
            tmpl,
            stem,
            f"src/{pascal}.g4",
            "src/Main.java",
            "{stem}.bash",
            "docs/{stem}.adoc",
        )
    )


def _spec_files(puffs: list[str]) -> list[str]:
    return ["%{_datadir}/%{name}/"]


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.tests", "tests/ present")]
    return [
        Finding(
            "note",
            "lang.tests",
            "no tests/ directory",
            "tests/",
            fix="Add tests/TestCommons.java or fixture checks for parser output.",
        )
    ]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".g4": 10.0},
    name_weights={"SomePuff1.g4": 4.0},
    depends=((re.compile(r"\b(default-jdk|antlr4|antlr)\b", re.I), 12.0),),
    meson_hints=(("find_program('antlr4'", 18.0), (".g4", 8.0)),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
    spec_files_fn=_spec_files,
    score_fn=_score_antlr,
)
