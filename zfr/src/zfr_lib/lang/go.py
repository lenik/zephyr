# SPDX-License-Identifier: AGPL-3.0-or-later
"""Go template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "go"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_dir_if_exists(tmpl, f"cmd/{stem}"), puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "go.mod").is_file():
        return []
    return [Finding("error", "lang.go.mod", "missing go.mod", "go.mod",
        fix="Add go.mod; meson should `go build` with -X main.buildVersion from meson.project_version().")]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".go": 4.0},
    name_weights={"go.mod": 30.0, "go.sum": 8.0},
    depends=((re.compile(r"\bgolang(?:-go)?\b", re.I), 12.0),),
    wire=WireSpec(kind="go"),
    puff_fn=_puff,
    lint_fn=_lint,
)
