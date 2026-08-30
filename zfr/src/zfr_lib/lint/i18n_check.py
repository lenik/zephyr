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
from ..l10n import (
    EN_MAN_NAME,
    canonical_locale,
    linguas_for_level,
    parse_l10n_level,
    resolve_present_locale,
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
                _("l10n level %s: no locale coverage required") % level,
            )
        ]

    out: list[Finding] = []
    out.append(
        Finding(
            "ok",
            "i18n.l10n-level",
            _("l10n level %(level)s (%(count)d locales)")
            % {"level": level, "count": len(required)},
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
                _("no po/ directory (optional unless the project uses gettext)"),
                fix=_("If the app is translated, add po/ with LINGUAS + *.po and "
                "i18n.gettext() in meson.build. Required locales at "
                "%(level)s: %(locales)s (source language %(source)s).")
                % {
                    "level": level,
                    "locales": ", ".join(required),
                    "source": RECOMMENDED_I18N_SOURCE,
                },
            )
        )
    else:
        linguas_path = po / "LINGUAS"
        present = set(_parse_linguas(linguas_path))
        if not present:
            out.append(
                Finding(
                    "warn",
                    "i18n.linguas",
                    _("po/ exists but po/LINGUAS is missing or empty"),
                    "po/LINGUAS",
                    fix=_("Create po/LINGUAS listing at least:\n%(locales)s\n"
                    "(English/%(source)s is the msgid source and is not listed.)")
                    % {
                        "locales": "\n".join(required),
                        "source": RECOMMENDED_I18N_SOURCE,
                    },
                )
            )
        else:
            missing = [
                loc
                for loc in required
                if resolve_present_locale(loc, present) is None
            ]
            if missing:
                out.append(
                    Finding(
                        "warn",
                        "i18n.linguas.coverage",
                        _("po/LINGUAS missing %(level)s locale(s): %(locales)s")
                        % {"level": level, "locales": ", ".join(missing)},
                        "po/LINGUAS",
                        fix=_("Level %(level)s requires primaries: %(locales)s "
                        "(source %(source)s; legacy es→es_MX, pt→pt_BR). "
                        "Run `zfr i18n -b` to auto-generate child locales.")
                        % {
                            "level": level,
                            "locales": ", ".join(missing),
                            "source": RECOMMENDED_I18N_SOURCE,
                        },
                    )
                )
            else:
                out.append(
                    Finding(
                        "ok",
                        "i18n.linguas.coverage",
                        _("po/LINGUAS covers %s primary locale set") % level,
                        "po/LINGUAS",
                    )
                )

            missing_po = []
            for loc in required:
                resolved = resolve_present_locale(loc, present)
                if resolved is None:
                    continue
                if not (po / f"{resolved}.po").is_file():
                    missing_po.append(loc)
            if missing_po:
                out.append(
                    Finding(
                        "warn",
                        "i18n.po.files",
                        _("LINGUAS entries without po/<locale>.po: %s") % ", ".join(missing_po),
                        "po/",
                        fix=_("For each locale: msginit -i <domain>.pot -o po/<locale>.po "
                        "-l <locale> --no-translator && msgmerge -U --no-wrap po/<locale>.po <domain>.pot"),
                    )
                )
            else:
                covered = [
                    loc
                    for loc in required
                    if resolve_present_locale(loc, present)
                    and (po / f"{resolve_present_locale(loc, present)}.po").is_file()
                ]
                if covered:
                    out.append(
                        Finding(
                            "ok",
                            "i18n.po.files",
                            _("%(level)s locale .po files present (%(count)d)")
                            % {"level": level, "count": len(covered)},
                            "po/",
                        )
                    )

            from ..translate.po_format import po_has_line_wrapping

            wrapped: list[str] = []
            for po_file in sorted(po.glob("*.po")):
                try:
                    if po_has_line_wrapping(po_file.read_text(encoding="utf-8")):
                        wrapped.append(po_file.name)
                except OSError:
                    continue
            if wrapped:
                out.append(
                    Finding(
                        "warn",
                        "i18n.po.wrap",
                        _("gettext catalogs use line wrapping: %s") % ", ".join(wrapped),
                        "po/",
                        fix=_("Run `zfr ize` (ZI016) or `msgcat --no-wrap -o file.po file.po` "
                        "on each catalog; use msgmerge --no-wrap when updating from .pot."),
                    )
                )
            elif list(po.glob("*.po")):
                out.append(
                    Finding(
                        "ok",
                        "i18n.po.wrap",
                        _("gettext catalogs use --no-wrap (no line wrapping)"),
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
                resolved = resolve_present_locale(loc, set(_parse_linguas(po / "LINGUAS"))) if po.is_dir() else None
                man_loc = resolved or canonical_locale(loc)
                path = docs / man_loc / adoc.name
                rel = f"docs/{man_loc}/{adoc.name}"
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
                    _("missing whole-document man translations for %(level)s: %(files)s")
                    % {"level": level, "files": ", ".join(missing_man)},
                    "docs/",
                    fix=_("Hand-translate docs/<locale>/<name>.adoc (full document, not po4a). "
                    "%(level)s requires: %(locales)s.")
                    % {"level": level, "locales": ", ".join(required)},
                )
            )
        else:
            out.append(
                Finding(
                    "ok",
                    "i18n.man.coverage",
                    _("%s whole-document man translations present") % level,
                    "docs/",
                )
            )
        if english_copies:
            out.append(
                Finding(
                    "warn",
                    "i18n.man.english-copy",
                    _("man translation still contains the English Name line: %s")
                    % ", ".join(english_copies),
                    "docs/",
                    fix=_("Translate the Name line; do not leave the English wording."),
                )
            )

    return out
