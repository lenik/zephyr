# SPDX-License-Identifier: AGPL-3.0-or-later
"""C library (clib) template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "clib"


def _score_clib(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    ok = bool(re.search(r"\bshared_library\s*\(", meson_txt))
    ok = ok or (re.search(r"\bpkgconfig\.generate\s*\(", meson_txt) and (root / "src" / "lib.c").is_file())
    ok = ok or ((root / "src" / "lib.c").is_file() and re.search(
        r"\bbas-c\b|\blibbas-c(?:-dev)?\b", meson_txt + "\n" + depends, re.I))
    if ok:
        scores["clib"] += 22.0
        scores["c"] *= 0.2
    else:
        if scores["c"]:
            scores["c"] += 4.0
        scores["clib"] *= 0.2

def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.c", "src/{stem}.h", "tests/{stem}_test.c", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.tests", "tests/ present")]
    return [Finding("note", "lang.tests", "no tests/ directory", "tests/",
        fix="Add tests/ and meson test() entries like the C family templates.")]

def _spec_files(puffs: list[str]) -> list[str]:
    return [
        "%{_libdir}/lib%{name}.so*",
        "%{_libdir}/pkgconfig/%{name}.pc",
        "%{_libdir}/pkgconfig/%{name}-static.pc",
        "%{_includedir}/%{name}/",
    ]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".c": 2.0, ".h": 0.45},
    depends=((re.compile(r"\blibbas-c-dev\b", re.I), 16.0),),
    meson_tokens={"c": 18.0, "clib": 18.0},
    wire=WireSpec(kind="c", app_ext="c", test_ext="c"),
    puff_fn=_puff,
    lint_fn=_lint,
    score_fn=_score_clib,
    spec_files_fn=_spec_files,
    skip_shared_example=True,
)
