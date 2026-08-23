# SPDX-License-Identifier: AGPL-3.0-or-later
"""TypeScript template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "typescript"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.ts", "src/{stem}.sh.in", "docs/{stem}.adoc", "{stem}.bash", "po/{stem}.pot"))

def _spec_files(puffs: list[str]) -> list[str]:
    p = puffs[0] if puffs else "zephyr"
    return ["%{_datadir}/%{name}/", f"%{{_infodir}}/{p}.info*"]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".ts": 4.0, ".tsx": 4.0, ".cts": 3.0, ".mts": 3.0, ".js": 0.35, ".mjs": 0.35, ".cjs": 0.35},
    name_weights={"package.json": 10.0, "tsconfig.json": 25.0, "pnpm-lock.yaml": 5.0, "package-lock.json": 5.0, "yarn.lock": 5.0},
    shebangs=((re.compile(r"^#!.*\bnode\b"), 1.5),),
    depends=((re.compile(r"\b(nodejs|npm|node-typescript|typescript)\b", re.I), 10.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    spec_files_fn=_spec_files,
)
