# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize engine helpers — gettext / man-locale coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Ize


def ensure_po_no_wrap(ize: "Ize") -> None:
    from ...translate.po_format import po_has_line_wrapping, po_no_wrap_file, po_prepare_utf8, read_po_text

    po_dir = ize.root / "po"
    if not po_dir.is_dir():
        return
    for po in sorted(po_dir.glob("*.po")):
        try:
            original_bytes = po.read_bytes()
            text = read_po_text(po)
        except OSError:
            continue
        updated = po_prepare_utf8(text)
        needs_write = updated.encode("utf-8") != original_bytes
        if not needs_write and not po_has_line_wrapping(text):
            continue
        rel = str(po.relative_to(ize.root))
        if ize.dry_run:
            ize.note("would-update", rel, "msgcat --no-wrap", rule="ize.i18n.po-nowrap")
            continue
        if po_no_wrap_file(po):
            ize.note("update", rel, "msgcat --no-wrap", rule="ize.i18n.po-nowrap")


def ensure_i18n_coverage(ize: "Ize") -> None:
    """Add missing LINGUAS / .po entries for the project's lint l10n level."""
    from ...l10n import linguas_for_level, project_l10n_level, resolve_present_locale
    from ...translate.po_files import insert_locale, parse_linguas

    po_dir = ize.root / "po"
    if not po_dir.is_dir():
        return
    level = project_l10n_level(ize.root)
    required = linguas_for_level(level)
    if not required:
        return
    present = set(parse_linguas(po_dir / "LINGUAS"))
    for loc in required:
        resolved = resolve_present_locale(loc, present)
        if resolved is not None and (po_dir / f"{resolved}.po").is_file():
            continue
        insert_name = resolved or loc
        if ize.dry_run:
            ize.note(
                "would-add",
                f"po/{insert_name}.po",
                f"{level} locale coverage",
                rule="ize.i18n.coverage",
            )
            continue
        try:
            changed = insert_locale(ize.root, insert_name)
        except (FileNotFoundError, OSError) as exc:
            ize.note("skip", "po/", str(exc), rule="ize.i18n.coverage")
            continue
        for rel in changed:
            ize.note("add", rel, f"{level} locale coverage", rule="ize.i18n.coverage")
        present = set(parse_linguas(po_dir / "LINGUAS"))


def ensure_man_locale_coverage(ize: "Ize") -> None:
    """Scaffold docs/<locale>/*.adoc for the project's lint l10n level.

    Copies the English whole-document man source when a locale file is
    missing so ZL055 is cleared; translators should replace the scaffold.
    """
    from ...l10n import (
        canonical_locale,
        linguas_for_level,
        project_l10n_level,
        resolve_present_locale,
    )
    from ...translate.po_files import parse_linguas

    docs = ize.root / "docs"
    if not docs.is_dir():
        return
    english = sorted(p for p in docs.glob("*.adoc") if p.is_file())
    if not english:
        return
    po_dir = ize.root / "po"
    if not po_dir.is_dir():
        return
    level = project_l10n_level(ize.root)
    required = linguas_for_level(level)
    if not required:
        return
    present = set(parse_linguas(po_dir / "LINGUAS"))
    for adoc in english:
        try:
            body = adoc.read_text(encoding="utf-8")
        except OSError:
            continue
        for loc in required:
            resolved = resolve_present_locale(loc, present) or canonical_locale(loc)
            dest = docs / resolved / adoc.name
            if dest.is_file():
                continue
            rel = str(dest.relative_to(ize.root))
            if ize.dry_run:
                ize.note(
                    "would-add",
                    rel,
                    f"{level} man locale scaffold from English",
                    rule="ize.i18n.man-locale",
                )
                continue
            ize.write_text(
                dest,
                body,
                f"{level} man locale scaffold from English",
            )


def derive_i18n_locales(ize: "Ize") -> None:
    from ...i18n.builder import default_build_po_dir, derive_locales
    from ...i18n.meson import ensure_po_meson_derive

    for rel in ensure_po_meson_derive(ize.root, dry_run=ize.dry_run):
        ize.note(
            "update" if not ize.dry_run else "would-update",
            rel,
            "Meson build runs zfr i18n -b into build dir",
            rule="ize.i18n.derive",
        )
    po_dir = default_build_po_dir(ize.root)
    written = derive_locales(ize.root, po_dir=po_dir, dry_run=ize.dry_run)
    for rel in written:
        ize.note(
            "would-derive" if ize.dry_run else "derive",
            rel,
            "child locale from parent",
            rule="ize.i18n.derive",
        )
