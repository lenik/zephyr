# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr lint — validate a project against zephyr packaging and layout style."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from i18n import _
from l10n import parse_l10n_level

NAME = "lint"
HELP = _("validate project packaging and zephyr layout (walks parents from cwd)")
DESCRIPTION = _(
    "Check the current zephyr project for missing files and packaging/style mistakes. "
    "Walks from cwd toward parent directories. CSR colors when stdout is a TTY. "
    "Style-contract blurbs default on for non-interactive stdout and AI-integrated "
    "terminals (Cursor, VS Code, Windsurf, …); off for a plain interactive shell. "
    "Override with -i/-I."
)


def collect_findings(root: Path, *, l10n_level: str = "L1"):
    from lint._cmd import collect_findings as _cf

    return _cf(root, l10n_level=l10n_level)


def cmd_lint(**kwargs) -> int:
    from lint._cmd import cmd_lint as _cl

    return _cl(**kwargs)


def add_arguments(p: argparse.ArgumentParser) -> None:
    from terminal import add_for_ai_purpose_arguments
    from lint.severity import parse_severity_level

    p.add_argument("-v", "--verbose", action="store_true", help=_("show passing checks too"))
    p.add_argument("-q", "--quiet", action="store_true", help=_("only print errors"))
    p.add_argument(
        "-b",
        "--browse",
        action="store_true",
        help=_(
            "open a local web UI with maximum-verbosity lint results, "
            "locale switcher, and per-finding [ize] actions"
        ),
    )
    p.add_argument(
        "-w",
        "--warning",
        nargs="?",
        const="note",
        default=None,
        type=parse_severity_level,
        metavar="LEVEL",
        dest="warning_level",
        help=_(
            "treat LEVEL as warning (LEVEL=note|warn|error; default note: "
            "note→warn; warn=no-op; error→warn)"
        ),
    )
    p.add_argument(
        "-e",
        "--error",
        nargs="?",
        const="warn",
        default=None,
        type=parse_severity_level,
        metavar="LEVEL",
        dest="error_level",
        help=_(
            "treat LEVEL as error (LEVEL=note|warn|error; default warn: "
            "warn→error; note→note+warn→error; error=no-op)"
        ),
    )
    p.add_argument(
        "--strict",
        action="store_const",
        const="warn",
        dest="error_level",
        help=_("alias for -e/--error=warn (treat warnings as errors)"),
    )
    p.add_argument(
        "-L",
        "--list-std",
        action="store_true",
        help=_("list numbered lint standards (ZL*) as a table and exit"),
    )
    p.add_argument(
        "-H",
        "--help-std",
        metavar="NUM",
        help=_("show details for lint standard NUM (e.g. ZL0026, 26) and exit"),
    )
    p.add_argument(
        "-l",
        "--l10n-level",
        metavar="LEVEL",
        type=parse_l10n_level,
        default=None,
        help=_(
            "required gettext/manpage locale coverage L0–L3 "
            "(default: L1; project file may override)"
        ),
    )
    info = p.add_mutually_exclusive_group()
    info.add_argument(
        "-i",
        "--info",
        dest="style_info",
        action="store_true",
        help=_("show zephyr style-contract / next-steps blurbs (default for pipes and AI terminals)"),
    )
    info.add_argument(
        "-I",
        "--no-info",
        dest="style_info",
        action="store_false",
        help=_("hide zephyr style-contract / next-steps blurbs (default for plain interactive shell)"),
    )
    p.set_defaults(style_info=None)
    add_for_ai_purpose_arguments(p)
    p.add_argument(
        "-u",
        "--uncheck",
        action="append",
        metavar="CODE",
        default=[],
        help=_("suppress rule ID(s) or code(s), comma-separated (repeatable)"),
    )
    p.add_argument(
        "-a",
        "--always",
        action="append",
        metavar="CODE",
        default=[],
        help=_("force-enable rule ID(s) or code(s) even if unchecked (repeatable)"),
    )
    p.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help=_("CSR (console SGR) highlighting (default: auto)"),
    )


def run(args: argparse.Namespace) -> int:
    from std import LINT_RULES, render_std_help, render_std_table
    from lib import find_project_dir
    from l10n import apply_lint_option_file
    from lint._cmd import _resolve_lint_root

    if args.list_std:
        sys.stdout.write(render_std_table(LINT_RULES.all_rules()))
        return 0
    if args.help_std:
        rule = LINT_RULES.by_id(args.help_std)
        if rule is None:
            print(_("unknown lint standard: %s") % args.help_std, file=sys.stderr)
            return 2
        sys.stdout.write(render_std_help(rule, command="lint"))
        return 0
    root = _resolve_lint_root(find_project_dir())
    parser = argparse.ArgumentParser(add_help=False)
    add_arguments(parser)
    args = apply_lint_option_file(root, parser, args)
    return cmd_lint(
        verbose=args.verbose,
        quiet=args.quiet,
        color=args.color,
        warning_level=getattr(args, "warning_level", None),
        error_level=getattr(args, "error_level", None),
        l10n_level=args.l10n_level or "L1",
        style_info=args.style_info,
        for_ai_purpose=getattr(args, "for_ai_purpose", None),
        uncheck=args.uncheck,
        always=getattr(args, "always", None),
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
