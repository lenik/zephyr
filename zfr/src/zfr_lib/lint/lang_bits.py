# SPDX-License-Identifier: AGPL-3.0-or-later
"""Language-specific lint bits."""

from __future__ import annotations

from pathlib import Path

from ..lang import lint_bits, skips_shared_example
from ..i18n import _
from .finding import Finding
from .util import _rel, _role, find_example_shared_modules


def check_lang_bits(root: Path, lang: str) -> list[Finding]:
    out: list[Finding] = []
    out.extend(lint_bits(lang, root, _role(root)))
    out.extend(_check_example_shared_modules(root, lang, _role(root)))
    return out


def _check_example_shared_modules(root: Path, lang: str, role: str) -> list[Finding]:
    if role == "meta" or skips_shared_example(lang):
        return []
    out: list[Finding] = []
    for path in find_example_shared_modules(root):
        if path.stem == "common_lib" or path.name.lower().startswith("common_lib."):
            out.append(
                Finding(
                    "warn",
                    "lang.shared.name",
                    _("legacy example module %s; use commons or a specific name") % path.name,
                    _rel(root, path),
                    fix=_("Rename to src/commons.* (template convention) or a project-specific "
                    "module name."),
                )
            )
    modules = find_example_shared_modules(root)
    if modules and not out:
        names = ", ".join(p.name for p in modules)
        out.append(
            Finding(
                "note",
                "lang.shared.example",
                _("%s is only a template example for shared helpers") % names,
                _rel(root, modules[0]),
                fix=_("common_lib / commons mean “extract reusable pieces”, but filenames should be "
                "concrete. Rename to a specific module in real projects (e.g. stream_copy.py, "
                "bulk.h). clib/cpplib keep lib.c/lib.cpp as their shared library entry."),
            )
        )
    return out
