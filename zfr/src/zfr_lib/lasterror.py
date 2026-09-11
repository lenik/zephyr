# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr lasterror — browse / replay the last ``zfr package`` run."""

from __future__ import annotations

import argparse
import sys

from .cli import register_command
from .fdm import FDMUX_MISSING, demux_file, page_files, which_fdm_tool
from .i18n import _
from .pkg_last import PackagerRecord, load_last_run, record_fdm_path
from .pkg_ui import interactive_lasterror, print_run_summary

NAME = "lasterror"
HELP = _("browse the last zfr package output interactively")
DESCRIPTION = _(
    "Show the last packaging run. Arrow keys select a packager; "
    "Tab opens the captured log in fdmpager; Enter replays that packager's "
    "stdout/stderr with fddemux; q quits."
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
        "-p",
        "--pager",
        action="store_true",
        help=_("view captured logs with fdmpager (requires fdmux)"),
    )
    p.add_argument(
        "--replay",
        metavar="KIND",
        default="",
        help=_("non-interactively replay KIND (deb, rpm, …) to stdout/stderr"),
    )


def _replay_record(rec: PackagerRecord) -> int:
    path = record_fdm_path(rec)
    if path is None:
        print(f"zfr lasterror: no FDM capture for {rec.name!r}", file=sys.stderr)
        return 1
    if not which_fdm_tool("fddemux"):
        print(FDMUX_MISSING, file=sys.stderr)
        return 1
    demux_file(path)
    return 0 if rec.ok else 1


def run(args: argparse.Namespace) -> int:
    last = load_last_run()
    if last is None or not last.records:
        print("zfr lasterror: no saved package run (run `zfr package` first)", file=sys.stderr)
        return 1

    if args.replay:
        want = args.replay.strip().lower()
        for rec in last.records:
            if rec.name == want:
                return _replay_record(rec)
        print(f"zfr lasterror: no packager named {want!r}", file=sys.stderr)
        return 1

    records = last.failures() if args.failures else list(last.records)
    if args.pager:
        if not records:
            print("zfr lasterror: no package records", file=sys.stderr)
            return 1
        if not which_fdm_tool("fdmpager"):
            print(FDMUX_MISSING, file=sys.stderr)
            return 1
        paths: list[str] = []
        for rec in records:
            p = record_fdm_path(rec)
            if p is not None:
                paths.append(str(p))
        if not paths:
            print("zfr lasterror: no FDM captures", file=sys.stderr)
            return 1
        page_files(paths)
        return 0 if not last.failures() else 1

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
