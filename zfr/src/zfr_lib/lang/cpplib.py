# SPDX-License-Identifier: AGPL-3.0-or-later
"""C++ library (cpplib) template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "cpplib"


def _score_cpplib(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    ok = bool(re.search(r"\bshared_library\s*\(", meson_txt))
    ok = ok or (re.search(r"\bpkgconfig\.generate\s*\(", meson_txt) and (root / "src" / "lib.cpp").is_file())
    ok = ok or ((root / "src" / "lib.cpp").is_file() and re.search(
        r"\bbas-cpp\b|\blibbas-cpp(?:-dev)?\b", meson_txt + "\n" + depends, re.I))
    if ok:
        scores["cpplib"] += 22.0
        scores["cpp"] *= 0.2
    else:
        if scores["cpp"]:
            scores["cpp"] += 4.0
        scores["cpplib"] *= 0.2

def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.cpp", "src/{stem}.hpp", "tests/{stem}_test.cpp", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.tests", _("tests/ present"))]
    return [Finding("note", "lang.tests", _("no tests/ directory"), "tests/",
        fix=_("Add tests/ and meson test() entries like the C family templates."))]

def _spec_files(puffs: list[str]) -> list[str]:
    return [
        "%{_libdir}/lib%{name}.so*",
        "%{_libdir}/pkgconfig/%{name}.pc",
        "%{_libdir}/pkgconfig/%{name}-static.pc",
        "%{_includedir}/%{name}/",
    ]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".cpp": 3.0, ".cc": 3.0, ".cxx": 3.0, ".hpp": 2.0, ".hh": 2.0, ".hxx": 2.0, ".h": 0.35},
    depends=((re.compile(r"\blibbas-cpp-dev\b", re.I), 16.0),),
    meson_tokens={"cpp": 18.0, "cpplib": 18.0},
    wire=WireSpec(kind="c", app_ext="cpp", test_ext="cpp"),
    puff_fn=_puff,
    lint_fn=_lint,
    score_fn=_score_cpplib,
    spec_files_fn=_spec_files,
    skip_shared_example=True,
)
