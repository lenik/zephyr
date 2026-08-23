# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext catalog coverage checks."""

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

def _parse_linguas(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for line in _read(path).splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def check_i18n(root: Path, role: str) -> list[Finding]:
    """Zephyr style: po/LINGUAS should cover the recommended locale set."""
    po = root / "po"
    if not po.is_dir():
        if role == "meta":
            return []
        return [
            Finding(
                "note",
                "i18n.po",
                "no po/ directory (optional unless the project uses gettext)",
                fix="If the app is translated, add po/ with LINGUAS + *.po and "
                "i18n.gettext() in meson.build. Recommended locales: "
                + ", ".join(RECOMMENDED_I18N_LINGUAS)
                + f" (source language {RECOMMENDED_I18N_SOURCE}).",
            )
        ]

    out: list[Finding] = []
    linguas_path = po / "LINGUAS"
    present = _parse_linguas(linguas_path)
    if not present:
        out.append(
            Finding(
                "warn",
                "i18n.linguas",
                "po/ exists but po/LINGUAS is missing or empty",
                "po/LINGUAS",
                fix="Create po/LINGUAS listing at least:\n"
                + "\n".join(RECOMMENDED_I18N_LINGUAS)
                + f"\n(English/{RECOMMENDED_I18N_SOURCE} is the msgid source and is not listed.)",
            )
        )
        return out

    missing = [loc for loc in RECOMMENDED_I18N_LINGUAS if loc not in present]
    if missing:
        out.append(
            Finding(
                "warn",
                "i18n.linguas.coverage",
                "po/LINGUAS missing recommended locale(s): " + ", ".join(missing),
                "po/LINGUAS",
                fix="Zephyr style recommends i18n at least includes: "
                + ", ".join(RECOMMENDED_I18N_LINGUAS)
                + f" (source {RECOMMENDED_I18N_SOURCE}; zh-cn→zh_CN, zh-tw→zh_TW). "
                "Append the missing lines to LINGUAS and add matching po/<locale>.po "
                "(msginit -i <domain>.pot -l <locale> --no-translator).",
            )
        )
    else:
        out.append(
            Finding(
                "ok",
                "i18n.linguas.coverage",
                "po/LINGUAS covers the recommended locale set",
                "po/LINGUAS",
            )
        )

    missing_po = [
        loc
        for loc in RECOMMENDED_I18N_LINGUAS
        if loc in present and not (po / f"{loc}.po").is_file()
    ]
    if missing_po:
        out.append(
            Finding(
                "warn",
                "i18n.po.files",
                "LINGUAS entries without po/<locale>.po: " + ", ".join(missing_po),
                "po/",
                fix="For each locale: msginit -i <domain>.pot -o po/<locale>.po "
                "-l <locale> --no-translator && msgmerge -U po/<locale>.po <domain>.pot",
            )
        )
    else:
        covered = [loc for loc in RECOMMENDED_I18N_LINGUAS if (po / f"{loc}.po").is_file()]
        if covered:
            out.append(
                Finding(
                    "ok",
                    "i18n.po.files",
                    f"recommended locale .po files present ({len(covered)})",
                    "po/",
                )
            )
    return out
