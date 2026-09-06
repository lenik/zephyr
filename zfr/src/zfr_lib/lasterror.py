# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr lasterror — browse / replay the last ``zfr package`` run."""

from __future__ import annotations

import argparse
import sys

from .cli import register_command
from .i18n import _
from .pkg_last import load_last_run
from .pkg_ui import interactive_lasterror, print_run_summary
from .stream_mark import replay_marked

NAME = "lasterror"
HELP = _("browse the last zfr package output interactively")
DESCRIPTION = _(
    "Show the last parallel packaging run. Arrow keys select a packager; "
    "Tab opens full captured output; Enter replays that packager's "
    "stdout/stderr in original order; q quits."
)


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-f",
        "--failures",
        action="store_true",
        help=_("list only failed packagers"),
    )
    p.add_argument(
        "-n",
        "--non-interactive",
        action="store_true",
        help=_("print a summary and exit (no curses UI)"),
    )
    p.add_argument(
        "--replay",
        metavar="KIND",
        default="",
        help=_("non-interactively replay KIND (deb, rpm, …) to stdout/stderr"),
    )


def run(args: argparse.Namespace) -> int:
    last = load_last_run()
    if last is None or not last.records:
        print("zfr lasterror: no saved package run (run `zfr package` first)", file=sys.stderr)
        return 1

    if args.replay:
        want = args.replay.strip().lower()
        for rec in last.records:
            if rec.name == want:
                replay_marked(rec.marked)
                return 0 if rec.ok else 1
        print(f"zfr lasterror: no packager named {want!r}", file=sys.stderr)
        return 1

    if args.non_interactive or not sys.stdin.isatty() or not sys.stdout.isatty():
        print_run_summary(last)
        return 0 if not last.failures() else 1

    return interactive_lasterror(last, only_failures=bool(args.failures))


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
