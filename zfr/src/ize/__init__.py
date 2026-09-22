# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr ize — bring an existing project up to current zephyr style."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from i18n import _

NAME = "ize"
HELP = _("refactor this project to current zephyr style")
DESCRIPTION = _(
    "Refactor the current project to match current zephyr style: missing debian/rpm files, "
    "meson targets, AsciiDoc man pages, Meson version substitutions, and lint-level gettext "
    "coverage (LINGUAS + .po). Does not scaffold man/<locale> man translations. Walks from cwd toward parents."
)


def cmd_ize(**kwargs) -> int:
    from ize._cmd import cmd_ize as _cmd

    return _cmd(**kwargs)


def add_arguments(p: argparse.ArgumentParser) -> None:
    from lang import LANGS

    p.add_argument(
        "-l",
        "--lang",
        metavar="LANG",
        help=_("language template to align with (default: detect; one of: %s)")
        % ", ".join(LANGS),
    )
    p.add_argument(
        "-n", "--dry-run", action="store_true", help=_("print planned changes without writing files")
    )
    p.add_argument(
        "-L",
        "--list-std",
        action="store_true",
        help=_("list numbered ize standards (ZI*) as a table and exit"),
    )
    p.add_argument(
        "-H",
        "--help-std",
        metavar="NUM",
        help=_("show details for ize standard NUM (e.g. ZI0015, 15) and exit"),
    )
    p.add_argument(
        "-c",
        "--commit",
        action="store_true",
        help=_(
            "bump patch version (debian/changelog + VERSION), git add -A, "
            "and commit ize changes with a verbose message"
        ),
    )
    p.add_argument(
        "-a",
        "--author",
        metavar="AUTHOR",
        help=_(
            "changelog author for --commit (Name or 'Name <email>'); "
            "default: reuse the previous debian/changelog trailer"
        ),
    )
    p.add_argument("-v", "--verbose", action="store_true", help=_("also print skipped files"))
    p.add_argument(
        "-m",
        "--mesonize",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=_("run 2meson to convert Autotools/CMake to Meson when present (default: on)"),
    )
    p.add_argument(
        "--no-man",
        action="store_true",
        help=_("do not convert groff .1 man pages to man/*.adoc"),
    )
    p.add_argument(
        "--no-subst",
        action="store_true",
        help=_("do not turn hardcoded versions/paths into @VERSION@/@PREFIX@ / config.h"),
    )
    p.add_argument(
        "-b",
        "--browse",
        action="store_true",
        help=_("open a local browser UI for matching ize rules and EditList diffs"),
    )
    p.add_argument(
        "-u",
        "--uncheck",
        action="append",
        metavar="CODE",
        default=[],
        help=_("suppress ize rule ID(s) or code(s), comma-separated (repeatable)"),
    )
    p.add_argument(
        "--always",
        action="append",
        metavar="CODE",
        default=[],
        help=_("force-enable ize rule ID(s) or code(s) even if unchecked (repeatable)"),
    )
    p.add_argument(
        "-o",
        "--only",
        action="append",
        metavar="CODE",
        default=[],
        help=_("run only these ize rule ID(s) or code(s), comma-separated (repeatable)"),
    )
    p.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help=_("CSR (console SGR) highlighting (default: auto)"),
    )


def run(args: argparse.Namespace) -> int:
    from std import IZE_RULES, render_std_help, render_std_table
    from lib import find_project_dir
    from cmd_options import IZE_OPTIONS_REL, apply_option_file

    if args.list_std:
        sys.stdout.write(render_std_table(IZE_RULES.all_rules()))
        return 0
    if args.help_std:
        rule = IZE_RULES.by_id(args.help_std)
        if rule is None:
            print(_("unknown ize standard: %s") % args.help_std, file=sys.stderr)
            return 2
        sys.stdout.write(render_std_help(rule, command="ize"))
        return 0
    root = find_project_dir()
    parser = argparse.ArgumentParser(add_help=False)
    add_arguments(parser)
    args = apply_option_file(
        root, IZE_OPTIONS_REL, parser, args, merge_flags=("uncheck", "always", "only")
    )
    return cmd_ize(
        lang=args.lang,
        dry_run=args.dry_run,
        man=not args.no_man,
        subst=not args.no_subst,
        mesonize=args.mesonize,
        commit=args.commit,
        author=args.author,
        verbose=args.verbose,
        color=args.color,
        uncheck=args.uncheck,
        always=getattr(args, "always", None),
        only=getattr(args, "only", None),
        browse=bool(getattr(args, "browse", False)),
    )


def register(sub: argparse._SubParsersAction) -> None:
    from cli import register_command

    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
