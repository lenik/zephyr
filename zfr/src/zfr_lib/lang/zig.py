# SPDX-License-Identifier: AGPL-3.0-or-later
"""Zig template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "zig"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/main.zig", "{stem}.bash", "docs/{stem}.adoc"))


def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "build.zig").is_file():
        return []
    return [Finding("error", "lang.zig.build", _("missing build.zig"), "build.zig",
        fix=_("Add build.zig; meson should invoke `zig build -Doptimize=ReleaseFast`."))]


SPEC = LangSpec(
    name=NAME,
    ext_weights={".zig": 4.0, ".zon": 2.0},
    name_weights={"build.zig": 30.0, "build.zig.zon": 10.0},
    depends=((re.compile(r"\bzig\b", re.I), 12.0),),
    meson_tokens={"zig": 18.0},
    meson_hints=(("find_program('zig'", 16.0), ("zig build", 14.0)),
    wire=WireSpec(kind="go"),
    puff_fn=_puff,
    lint_fn=_lint,
)
