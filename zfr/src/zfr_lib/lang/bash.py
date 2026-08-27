# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bash template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "bash"


def _score_bash(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    if re.search(r"\bbash-shlib\b", depends, re.I):
        scores["bash"] += 14.0
        return
    # Autotools m4-macro / data-only packages (e.g. libm4-xjl): treat as bash
    # so ize can scaffold debian/rpm around install_data of *.m4.
    m4s = list(root.rglob("*.m4"))
    # Note: any(root.rglob(ext) for …) is always True (generator objects are
    # truthy); check for an actual match instead.
    has_code = any(
        next(root.rglob(ext), None) is not None
        for ext in ("*.c", "*.py", "*.java", "*.pl", "*.rs")
    )
    if m4s and not has_code:
        # Ignore aclocal leftovers under m4/
        real = [p for p in m4s if "aclocal" not in p.name and p.name != "libtool.m4"]
        if len(real) >= 2:
            scores["bash"] += 12.0
            return
    from .. import iter_files
    src = root / "src"
    bases = [root] + ([src] if src.is_dir() else [])
    for base in bases:
        try:
            paths = [p for p in base.iterdir() if p.is_file()] if base == root else list(iter_files(base))
        except OSError:
            continue
        for path in paths:
            try:
                head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
            except OSError:
                continue
            if re.search(r"\bimport\s+cliboot\b", head) or re.search(
                r"(?:^|\n)\s*\. shlib(?:-import)?\b|\bshlib-import\b", head
            ):
                scores["bash"] += 14.0
                return

def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.in", "{stem}.bash", "docs/{stem}.adoc"))

def _lint(root: Path, role: str) -> list[Finding]:
    ins = list((root / "src").glob("*.in")) if (root / "src").is_dir() else []
    if ins:
        return [Finding("ok", "lang.bash.src", _("src scripts: %s") % ", ".join(p.name for p in ins))]
    return [Finding("warn", "lang.bash.src", _("no src/*.in scripts"), "src/",
        fix=_("Keep configured scripts as src/<puff>.in with @PACKAGE@/@VERSION@ "
        "and meson configure_file + install_mode rwxr-xr-x."))]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".sh": 1.2, ".bash": 3.0},
    shebangs=((re.compile(r"^#!.*\b(bash|sh)\b"), 3.0),),
    depends=((re.compile(r"\bbash-shlib\b", re.I), 18.0), (re.compile(r"\bbash\b", re.I), 8.0)),
    wire=WireSpec(kind="script", app_list="app_scripts", script_ext="in"),
    puff_fn=_puff,
    lint_fn=_lint,
    score_fn=_score_bash,
)
