# SPDX-License-Identifier: AGPL-3.0-or-later
"""Python template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "python"


def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.py", "tests/test_{stem}.py", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.python.tests", _("tests/ present"))]
    return [Finding("warn", "lang.python.tests", _("no tests/ (python template uses unittest + meson test)"), "tests/",
        fix=_("Add tests/test_*.py and meson test() with PYTHONPATH=src."))]

def _spec_files(puffs: list[str]) -> list[str]:
    return ["%{_bindir}/commons.py"]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".py": 3.0, ".pyi": 1.5},
    shebangs=((re.compile(r"^#!.*\bpython(?:3(?:\.\d+)?)?\b"), 4.0),),
    depends=((re.compile(r"\bpython3(?:-dev)?\b", re.I), 10.0),),
    meson_tokens={"python": 18.0},
    meson_hints=(("import('python')", 16.0), ('import("python")', 16.0)),
    wire=WireSpec(kind="python"),
    puff_fn=_puff,
    lint_fn=_lint,
    spec_files_fn=_spec_files,
)
