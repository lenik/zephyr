# SPDX-License-Identifier: AGPL-3.0-or-later
"""GNU C extensions template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "gcc"


def _score_gcc(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    markers = "gnu11" in meson_txt or "-std=gnu" in meson_txt
    src = root / "src"
    if src.is_dir():
        for path in src.glob("*.c"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "__attribute__" in text or "typeof(" in text:
                markers = True
                break
    if markers:
        scores["gcc"] += 22.0
        scores["c"] *= 0.2


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(
            tmpl,
            stem,
            "src/{stem}.c",
            "tests/{stem}_test.c",
            "{stem}.bash",
            "docs/{stem}.adoc",
        )
    )


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.tests", "tests/ present")]
    return [
        Finding(
            "note",
            "lang.tests",
            "no tests/ directory",
            "tests/",
            fix="Add tests/ and meson test() entries like the C family templates.",
        )
    ]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".c": 2.0},
    meson_tokens={"gcc": 18.0},
    meson_hints=(("-std=gnu11", 14.0),),
    wire=WireSpec(kind="c", app_ext="c", test_ext="c"),
    puff_fn=_puff,
    lint_fn=_lint,
    score_fn=_score_gcc,
)
