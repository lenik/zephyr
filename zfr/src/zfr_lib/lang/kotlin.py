# SPDX-License-Identifier: AGPL-3.0-or-later
"""Kotlin template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "kotlin"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/Main.kt", "{stem}.bash", "docs/{stem}.adoc"))


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.kotlin.tests", _("tests/ present"))]
    return [Finding("warn", "lang.kotlin.tests", _("no tests/ (kotlin template uses kotlinc + meson test)"), "tests/",
        fix=_("Add tests/Test*.kt and meson test() compiling with kotlinc."))]


def _spec_files(puffs: list[str]) -> list[str]:
    return ["%{_bindir}/some_puff1.jar", "%{_bindir}/some_puff1"]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".kt": 4.0, ".kts": 2.0},
    name_weights={"build.gradle.kts": 8.0, "build.gradle": 12.0},
    depends=((re.compile(r"\b(kotlin|default-jdk|openjdk)\b", re.I), 12.0),),
    meson_tokens={"kotlinc": 18.0},
    meson_hints=((".kt", 8.0), ("find_program('kotlinc'", 16.0)),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
    spec_files_fn=_spec_files,
)
