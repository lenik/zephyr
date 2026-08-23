# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rust template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "rust"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/main.rs", "src/lib.rs", "build-aux/cargo-build.sh", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "Cargo.toml").is_file():
        return []
    return [Finding("error", "lang.rust.cargo", "missing Cargo.toml", "Cargo.toml",
        fix="Rust zephyr projects keep Cargo.toml plus meson custom_target for the binary.")]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".rs": 4.0},
    name_weights={"cargo.toml": 30.0, "cargo.lock": 8.0},
    depends=((re.compile(r"\b(cargo|rustc)\b", re.I), 12.0),),
    meson_tokens={"rust": 20.0},
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
)
