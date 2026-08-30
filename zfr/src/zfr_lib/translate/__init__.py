# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr translate — query and update gettext message strings."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import find_project_dir
from ..cli import register_command
from ..csr import Csr
from ..i18n import _
from ..l10n import format_locale_display, normalize_locale
from .fmt import (
    paint,
    paint_key,
    paint_locale_label,
    paint_sep,
    paint_translation,
    stripe_fg,
)
from .po_files import (
    MatchField,
    catalog_matches,
    compile_match_pattern,
    group_catalog_rows,
    implemented_locales,
    list_matching_msgids,
    list_msgids,
    lookup_translation,
    update_translation,
)


def _read_stdin_text() -> str:
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read()


def cmd_import_poedit(path: Path) -> int:
    poedit = shutil.which("poedit")
    if poedit is None:
        print(_("poedit not found in PATH"), file=sys.stderr)
        return 1
    if not path.is_file():
        print(_("file not found: %s") % path, file=sys.stderr)
        return 1
    proc = subprocess.run([poedit, str(path)], check=False)
    return proc.returncode


def cmd_list_keys(
    root: Path,
    pattern: re.Pattern[str] | None,
    *,
    color: bool,
    entire: bool = False,
) -> int:
    msgids = (
        list_matching_msgids(root, pattern, entire=entire)
        if pattern
        else list_msgids(root)
    )
    for index, mid in enumerate(msgids):
        print(paint(mid, stripe_fg(index, on=color)))
    return 0


def _print_grouped_matches(
    groups: list[tuple[str, list[tuple[str, str]]]],
    *,
    color: bool,
) -> None:
    for index, (mid, locales) in enumerate(groups):
        if index:
            print()
        print(paint_key(mid, on=color))
        for loc, ms in locales:
            disp = format_locale_display(loc)
            text = ms if ms else mid
            print(
                f"{paint_locale_label(disp, loc, on=color)}"
                f"{paint_sep(': ', on=color)}"
                f"{paint_translation(text, loc, on=color)}"
            )


def cmd_catalog_search(
    root: Path,
    pattern: re.Pattern[str],
    *,
    lang: str | None,
    field: MatchField,
    color: bool,
    entire: bool = False,
) -> int:
    rows = catalog_matches(root, pattern, lang=lang, field=field, entire=entire)
    order = (
        list_matching_msgids(root, pattern, entire=entire)
        if field == "msgid"
        else None
    )
    groups = group_catalog_rows(rows, msgid_order=order)
    _print_grouped_matches(groups, color=color)
    return 0


def cmd_query(root: Path, text: str, *, lang: str | None, color: bool) -> int:
    locales = [normalize_locale(lang)] if lang else implemented_locales(root)
    if not locales:
        print(text)
        return 0
    for loc in locales:
        trans = lookup_translation(root, loc, text)
        label = format_locale_display(loc)
        value = trans if trans is not None else text
        line = (
            f"{paint_locale_label(label, loc, on=color)}"
            f"{paint_sep(': ', on=color)}"
            f"{paint_translation(value, loc, on=color)}"
        )
        print(line)
    return 0


def cmd_update(root: Path, lang: str, msgid: str, msgstr: str) -> int:
    path = update_translation(root, lang, msgid, msgstr)
    if path is None:
        print(_("no catalog for locale: %s") % lang, file=sys.stderr)
        return 1
    print(path.relative_to(root))
    return 0


NAME = "translate"
HELP = _("query and update gettext message strings")
DESCRIPTION = _(
    "Look up translations for TEXT across implemented locales, or update a "
    "single locale catalog. Remaining arguments are joined with spaces."
)


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-i",
        "--import",
        dest="import_file",
        metavar="FILE",
        type=Path,
        help=_("use poedit to import edits from FILE"),
    )
    p.add_argument(
        "-l",
        "--lang",
        metavar="LANG",
        help=_("query LANG only (default: all implemented; ignored for --import)"),
    )
    p.add_argument(
        "-u",
        "--update",
        metavar="LANG",
        help=_("update LANG with TRANSLATION (stdin if omitted)"),
    )
    p.add_argument(
        "-k",
        "--keys",
        action="store_true",
        help=_("list all message ids (msgids)"),
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "-m",
        "--match",
        metavar="REGEX",
        help=_("list msgids matching REGEX, case-insensitive (keys only with -k)"),
    )
    mode.add_argument(
        "-M",
        "--match-cs",
        metavar="REGEX",
        help=_("list msgids matching REGEX, case-sensitive (keys only with -k)"),
    )
    mode.add_argument(
        "-s",
        "--search",
        metavar="REGEX",
        help=_("list msgids/translations matching REGEX, case-insensitive (keys only with -k)"),
    )
    mode.add_argument(
        "-S",
        "--search-cs",
        metavar="REGEX",
        help=_("list msgids/translations matching REGEX, case-sensitive (keys only with -k)"),
    )
    p.add_argument(
        "-E",
        "--entire",
        action="store_true",
        help=_("with -m/-M/-s/-S, match the full msgid or translation (not a substring)"),
    )
    p.add_argument(
        "-c",
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help=_("CSR (console SGR) highlighting (default: auto)"),
    )
    p.add_argument("args", nargs="*", help=_("TEXT [TRANSLATION]"))


def run(args: argparse.Namespace) -> int:
    if args.import_file:
        return cmd_import_poedit(args.import_file)

    root = find_project_dir()
    color = Csr(args.color).on
    entire = bool(args.entire)

    pattern_src = args.match or args.match_cs or args.search or args.search_cs
    if args.match or args.match_cs:
        field: MatchField = "msgid"
        case_sensitive = bool(args.match_cs)
    elif args.search or args.search_cs:
        field = "both"
        case_sensitive = bool(args.search_cs)
    else:
        field = "msgid"
        case_sensitive = False

    pattern = (
        compile_match_pattern(pattern_src, case_sensitive=case_sensitive)
        if pattern_src
        else None
    )

    if args.keys:
        return cmd_list_keys(root, pattern, color=color, entire=entire)

    rest = list(args.args)

    if args.update:
        if not rest:
            print(_("TEXT required with --update"), file=sys.stderr)
            return 2
        msgid = rest[0]
        msgstr = " ".join(rest[1:]) if len(rest) > 1 else _read_stdin_text()
        if not msgstr:
            print(_("TRANSLATION required (args or stdin) with --update"), file=sys.stderr)
            return 2
        return cmd_update(root, args.update, msgid, msgstr)

    if pattern is not None:
        return cmd_catalog_search(
            root,
            pattern,
            lang=args.lang,
            field=field,
            color=color,
            entire=entire,
        )

    text = " ".join(rest)
    if not text and not sys.stdin.isatty():
        text = _read_stdin_text().rstrip("\n")
    if not text:
        print(_("TEXT required"), file=sys.stderr)
        return 2
    return cmd_query(root, text, lang=args.lang, color=color)


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
