# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lua template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "lua"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.lua", "tests/test_{stem}.lua", "{stem}.bash", "docs/{stem}.adoc"))


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.lua.tests", "tests/ present")]
    return [Finding("warn", "lang.lua.tests", "no tests/ (lua template uses lua tests + meson test)", "tests/",
        fix="Add tests/test_*.lua and meson test() invoking lua with LUA_PATH=src/?.lua.")]


def _spec_files(puffs: list[str]) -> list[str]:
    return ["%{_bindir}/commons.lua"]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".lua": 4.0},
    shebangs=((re.compile(r"^#!.*\b(luajit|lua)\b"), 4.0),),
    depends=((re.compile(r"\b(luajit|lua5(?:\.\d+)?|lua)\b", re.I), 12.0),),
    meson_tokens={"lua": 16.0, "luajit": 16.0},
    meson_hints=(("find_program('lua'", 14.0), ("find_program('luajit'", 14.0)),
    wire=WireSpec(kind="python"),
    puff_fn=_puff,
    lint_fn=_lint,
    spec_files_fn=_spec_files,
)
