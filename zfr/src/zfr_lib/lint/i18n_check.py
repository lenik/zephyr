# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext catalog coverage checks."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import (
    LANGS,
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
from ..l10n import EN_MAN_NAME, linguas_for_level, parse_l10n_level
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


def check_i18n(root: Path, role: str, *, l10n_level: str = "L1") -> list[Finding]:
    """Require gettext + whole-document man translations for the lint l10n level."""
    try:
        level = parse_l10n_level(l10n_level)
    except (argparse.ArgumentTypeError, ValueError, TypeError):
        level = "L1"
    required = linguas_for_level(level)
    if level == "L0" or not required:
        return [
            Finding(
                "ok",
                "i18n.l10n-level",
                f"l10n level {level}: no locale coverage required",
            )
        ]

    out: list[Finding] = []
    out.append(
        Finding(
            "ok",
            "i18n.l10n-level",
            f"l10n level {level} ({len(required)} locales)",
        )
    )

    po = root / "po"
    if not po.is_dir():
        if role == "meta":
            return out
        out.append(
            Finding(
                "note",
                "i18n.po",
                "no po/ directory (optional unless the project uses gettext)",
                fix="If the app is translated, add po/ with LINGUAS + *.po and "
                "i18n.gettext() in meson.build. Required locales at "
                f"{level}: " + ", ".join(required)
                + f" (source language {RECOMMENDED_I18N_SOURCE}).",
            )
        )
    else:
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
                    + "\n".join(required)
                    + f"\n(English/{RECOMMENDED_I18N_SOURCE} is the msgid source and is not listed.)",
                )
            )
        else:
            missing = [loc for loc in required if loc not in present]
            if missing:
                out.append(
                    Finding(
                        "warn",
                        "i18n.linguas.coverage",
                        f"po/LINGUAS missing {level} locale(s): " + ", ".join(missing),
                        "po/LINGUAS",
                        fix=f"Level {level} requires: "
                        + ", ".join(required)
                        + f" (source {RECOMMENDED_I18N_SOURCE}; zh-cn→zh_CN, zh-tw→zh_TW). "
                        "Append the missing lines to LINGUAS and add matching po/<locale>.po.",
                    )
                )
            else:
                out.append(
                    Finding(
                        "ok",
                        "i18n.linguas.coverage",
                        f"po/LINGUAS covers {level} locale set",
                        "po/LINGUAS",
                    )
                )

            missing_po = [
                loc
                for loc in required
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
                covered = [loc for loc in required if (po / f"{loc}.po").is_file()]
                if covered:
                    out.append(
                        Finding(
                            "ok",
                            "i18n.po.files",
                            f"{level} locale .po files present ({len(covered)})",
                            "po/",
                        )
                    )

    docs = root / "docs"
    english_adocs = (
        [p for p in docs.glob("*.adoc") if p.is_file()] if docs.is_dir() else []
    )
    if english_adocs:
        missing_man: list[str] = []
        english_copies: list[str] = []
        for adoc in english_adocs:
            for loc in required:
                path = docs / loc / adoc.name
                rel = f"docs/{loc}/{adoc.name}"
                if not path.is_file():
                    missing_man.append(rel)
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except OSError:
                    missing_man.append(rel)
                    continue
                if EN_MAN_NAME in text:
                    english_copies.append(rel)
        if missing_man:
            out.append(
                Finding(
                    "warn",
                    "i18n.man.coverage",
                    f"missing whole-document man translations for {level}: "
                    + ", ".join(missing_man),
                    "docs/",
                    fix="Hand-translate docs/<locale>/<name>.adoc (full document, not po4a). "
                    f"{level} requires: " + ", ".join(required) + ".",
                )
            )
        else:
            out.append(
                Finding(
                    "ok",
                    "i18n.man.coverage",
                    f"{level} whole-document man translations present",
                    "docs/",
                )
            )
        if english_copies:
            out.append(
                Finding(
                    "warn",
                    "i18n.man.english-copy",
                    "man translation still contains the English Name line: "
                    + ", ".join(english_copies),
                    "docs/",
                    fix="Translate the Name line; do not leave the English wording.",
                )
            )

    return out
