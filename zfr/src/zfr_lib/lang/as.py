# SPDX-License-Identifier: AGPL-3.0-or-later
"""NASM x86-64 assembly template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "as"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(
        puff_paths(
            tmpl,
            stem,
            "src/{stem}.asm",
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
            fix=_("Add tests/smoke.sh and meson test() for stdin/stdout copy."),
        )
    ]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".asm": 5.0, ".inc": 2.5, ".s": 3.0},
    depends=((re.compile(r"\bnasm\b", re.I), 14.0),),
    meson_hints=(("find_program('nasm'", 18.0), ("'-f', 'elf64'", 12.0)),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
)
