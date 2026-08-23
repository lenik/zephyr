# SPDX-License-Identifier: AGPL-3.0-or-later
"""Meson build checks."""

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

def check_meson(root: Path, lang: str) -> list[Finding]:
    out: list[Finding] = []
    path = root / "meson.build"
    if not path.is_file():
        return out
    text = _read(path)
    rel = "meson.build"

    if re.search(r"^\s*project\s*\(", text, re.M):
        out.append(Finding("ok", "meson.project", "project() present", rel))
    else:
        out.append(
            Finding(
                "error",
                "meson.project",
                "meson.build has no project() call",
                rel,
                fix="project() must be the first Meson call. Copy the header from the language template.",
            )
        )

    if _AGPL in text:
        out.append(Finding("ok", "meson.license", f"license {_AGPL}", rel))
    else:
        out.append(
            Finding(
                "warn",
                "meson.license",
                "meson license is not AGPL-3.0-or-later",
                rel,
                line=_line_of(text, "license"),
                fix=f"Set license: '{_AGPL}' in project().",
            )
        )

    for var in ("project_author", "project_email", "project_year"):
        if var in text:
            out.append(Finding("ok", f"meson.{var}", f"{var} set", rel))
        else:
            out.append(
                Finding(
                    "warn",
                    f"meson.{var}",
                    f"missing {var} (used for man pages)",
                    rel,
                    fix=f"Set {var} next to project(), then pass -a project-author/email/year to asciidoctor.",
                )
            )

    if "zfr version" in text:
        out.append(Finding("ok", "meson.version_source", "version uses `zfr version`", rel))
    elif "git describe" in text:
        out.append(
            Finding(
                "warn",
                "meson.version_source",
                "version still uses inline git describe; zephyr style is `zfr version`",
                rel,
                line=_line_of(text, "git describe"),
                fix="In project(version: run_command(...)), prefer:\n"
                "  v=$(zfr version 2>/dev/null || true)\n"
                "  with fallback v=\"0.0.0\" # FIXED TO 0.0.0, DO NOT MODIFY\n"
                "See bash/meson.build in the zephyr tree.",
            )
        )
    else:
        out.append(
            Finding(
                "warn",
                "meson.version_source",
                "could not find `zfr version` or git describe in project version",
                rel,
                fix="Use `zfr version` for project() version (see bash/meson.build).",
            )
        )

    if 'FIXED TO 0.0.0' in text or 'v="0.0.0"' in text:
        out.append(Finding("ok", "meson.version_fallback", "0.0.0 fallback present", rel))
    else:
        out.append(
            Finding(
                "note",
                "meson.version_fallback",
                "no explicit 0.0.0 fallback for missing git/VERSION",
                rel,
                fix='Keep fallback v="0.0.0" # FIXED TO 0.0.0, DO NOT MODIFY',
            )
        )

    if "asciidoctor" in text:
        out.append(Finding("ok", "meson.asciidoctor", "asciidoctor man pages", rel))
    else:
        out.append(
            Finding(
                "error",
                "meson.asciidoctor",
                "meson.build does not invoke asciidoctor",
                rel,
                fix="find_program('asciidoctor') and custom_target(..., '-b', 'manpage', ...).",
            )
        )

    if re.search(r"run_target\s*\(\s*['\"]look['\"]", text):
        out.append(Finding("ok", "meson.look", "run_target look present", rel))
    else:
        out.append(
            Finding(
                "note",
                "meson.look",
                "no run_target('look') DESTDIR preview",
                rel,
                fix="Add run_target look that meson install's into a tempdir and runs tree (see templates).",
            )
        )

    if "bash-completion" in text:
        out.append(Finding("ok", "meson.completion_install", "installs bash-completion", rel))
    else:
        out.append(
            Finding(
                "warn",
                "meson.completion_install",
                "does not install bash-completion",
                rel,
                fix="install_data(..., install_dir: datadir / 'bash-completion' / 'completions', rename: command).",
            )
        )
    return out
