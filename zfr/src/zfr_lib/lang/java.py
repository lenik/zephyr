# SPDX-License-Identifier: AGPL-3.0-or-later
"""Java template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "java"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/Main.java", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _spec_files(puffs: list[str]) -> list[str]:
    return ["%{_datadir}/%{name}/"]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".java": 4.0},
    name_weights={"pom.xml": 18.0, "build.gradle": 12.0, "build.gradle.kts": 8.0},
    depends=((re.compile(r"\b(default-jdk|default-jre|openjdk|java-runtime)\b", re.I), 12.0),),
    meson_hints=((".java", 8.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    spec_files_fn=_spec_files,
)
