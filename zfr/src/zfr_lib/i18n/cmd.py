# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr i18n — manage implemented gettext locales."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .. import find_project_dir
from ..cli import register_command
from ..l10n import (
    LOCALE_TIER_LABEL,
    canonical_locale,
    children_of,
    derive_parent,
    fallback_chain,
    format_locale_display,
    normalize_locale,
)
from ..translate.po_files import (
    delete_locale,
    implemented_locales,
    insert_locale,
    po_stats,
    resolve_po_path,
)
from .builder import derive_children_of, derive_locales
from .messages import _


def cmd_list_implemented(root: Path) -> int:
    locales = implemented_locales(root)
    if not locales:
        print(_("no implemented locales (po/LINGUAS + po/*.po)"))
        return 0
    for loc in locales:
        print(format_locale_display(loc))
    return 0


def cmd_locale_info(root: Path, lang: str) -> int:
    loc = normalize_locale(lang)
    print(format_locale_display(loc))
    tier = LOCALE_TIER_LABEL.get(canonical_locale(loc), "")
    if tier:
        print(_("tier %(tier)s") % {"tier": tier})
    parent = derive_parent(loc)
    if parent:
        print(_("derived from: %(parent)s") % {"parent": parent})
    chain = fallback_chain(loc)
    if chain:
        print(_("fallback chain: %(chain)s") % {"chain": " -> ".join(chain)})
    kids = children_of(loc)
    if kids:
        print(_("children (->): %(kids)s") % {"kids": ", ".join(kids)})
    found = resolve_po_path(root, loc)
    if found:
        po_path, resolved = found
        print(_("catalog: %(path)s") % {"path": po_path.relative_to(root)})
        stats = po_stats(po_path)
        print(_("po stats: %(translated)d/%(total)d translated, %(missing)d missing")
              % stats)
    else:
        print(_("no .po catalog in this project"))
    return 0


def cmd_insert(root: Path, lang: str) -> int:
    try:
        changed = insert_locale(root, lang)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for rel in changed:
        print(rel)
    return 0


def cmd_delete(root: Path, lang: str) -> int:
    removed = delete_locale(root, lang)
    if not removed:
        print(_("locale not found: %s") % lang, file=sys.stderr)
        return 1
    for rel in removed:
        print(rel)
    return 0


def cmd_build(root: Path, *, lang: str | None, dry_run: bool, force: bool) -> int:
    if lang:
        written = derive_children_of(root, lang, dry_run=dry_run, force=force)
    else:
        written = derive_locales(root, dry_run=dry_run, force=force)
    if dry_run:
        print(_("would build %d derived locale file(s)") % len(written))
    else:
        for rel in written:
            print(rel)
    return 0


NAME = "i18n"
HELP = _("manage implemented gettext locales")
DESCRIPTION = _(
    "List, add, delete, and build derived locales in the current project. "
    "Use zfr translate to query or update message strings."
)


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-a",
        "--all",
        action="store_true",
        help=_("list all implemented locales in this project"),
    )
    p.add_argument(
        "-d",
        "--delete",
        metavar="LOCALE",
        help=_("delete a locale (LINGUAS, .po, docs/)"),
    )
    p.add_argument(
        "-i",
        "--insert",
        metavar="LANG",
        help=_("add a new locale"),
    )
    p.add_argument(
        "-b",
        "--build",
        action="store_true",
        help=_("build derived locale PO/man files from parents (skip locales in LINGUAS)"),
    )
    p.add_argument("-n", "--dry-run", action="store_true", help=_("with --build, print only"))
    p.add_argument("-f", "--force", action="store_true", help=_("with --build, overwrite existing"))
    p.add_argument("locale", nargs="?", metavar="LOCALE", help=_("locale to inspect"))


def run(args: argparse.Namespace) -> int:
    root = find_project_dir()
    if args.all:
        return cmd_list_implemented(root)
    if args.delete:
        return cmd_delete(root, args.delete)
    if args.insert:
        return cmd_insert(root, args.insert)
    if args.build:
        return cmd_build(root, lang=args.locale, dry_run=args.dry_run, force=args.force)
    if args.locale:
        return cmd_locale_info(root, args.locale)
    return cmd_list_implemented(root)


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
