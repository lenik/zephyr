# SPDX-License-Identifier: AGPL-3.0-or-later
"""Template-gap checks."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import (
    LANGS,
    RECOMMENDED_I18N_LINGUAS,
    RECOMMENDED_I18N_SOURCE,
    TEMPLATE_PUFF,
    _is_zfr_cli_package,
    _is_zfr_meta_repo,
    changelog_version,
    detect_lang,
    find_project_dir,
    is_probably_text,
    iter_files,
    template_dir,
    version_file_version,
)
from ..csr import Csr
from ..packaging import _meson_project_fields, _parse_control_stanzas
from .finding import Finding
from .util import *  # noqa: F403

def check_template_gaps(root: Path, lang: str, role: str) -> list[Finding]:
    """Warn about structural files the language template has that this tree lacks."""
    if role == "meta" or lang not in LANGS:
        return []
    if _is_zfr_cli_package(root):
        return [
            Finding(
                "ok",
                "template.coverage",
                "zfr CLI package is not a language template",
            )
        ]
    try:
        tmpl = template_dir(lang)
    except SystemExit:
        return []
    if tmpl.resolve() == root.resolve():
        return []
    skip_top = {
        "build",
        "rpmbuild",
        ".git",
        "CLAUDE.md",
        ".cursor",
        ".vscode",
    }
    missing: list[str] = []
    for path in iter_files(tmpl):
        rel = path.relative_to(tmpl)
        if rel.parts and rel.parts[0] in skip_top:
            continue
        if TEMPLATE_PUFF in path.name or TEMPLATE_PUFF in rel.as_posix():
            continue
        if not (root / rel).exists():
            # only flag well-known scaffolding, not every po locale
            if rel.parts[0] in {"debian", "docs", "src", "tests", "rpm", ".githooks"} or rel.name in {
                "meson.build",
                "LICENSE",
                "README.md",
                "README-zh.md",
                "VERSION",
            }:
                missing.append(rel.as_posix())
    if not missing:
        return [Finding("ok", "template.coverage", "structural files from the language template are present")]
    preview = ", ".join(missing[:12])
    more = "" if len(missing) <= 12 else f" (+{len(missing) - 12} more)"
    return [
        Finding(
            "note",
            "template.coverage",
            f"language template {lang} has extra scaffolding not in this tree: {preview}{more}",
            fix=f"Compare with the {lang} template under pkgdatadir. Copy missing debian/docs/src/rpm "
            "files, or `zfr add` puffs. Do not copy build/ or debian leftover stamp files.",
        )
    ]
