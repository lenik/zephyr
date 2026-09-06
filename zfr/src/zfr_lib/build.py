# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr build — detect build system and compile the project."""

from __future__ import annotations

import argparse
from pathlib import Path

from .buildsys import build_project, detect_build_system
from .cli import register_command
from .i18n import _
from .jobs import add_job_argument, resolve_jobs

NAME = "build"
HELP = _("detect build system and compile the project")
DESCRIPTION = _(
    "Detect the project build system (meson, cmake, autotools, cargo, go, npm, make) "
    "and run a local compile."
)


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-C",
        "--chdir",
        metavar="DIR",
        default="",
        help=_("change to DIR before detecting the build system"),
    )
    p.add_argument(
        "-b",
        "--builddir",
        metavar="DIR",
        default="",
        help=_("build directory (default: <project>/build)"),
    )
    add_job_argument(p)
    p.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help=_("print planned commands without running them"),
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=_("verbose build output where supported"),
    )
    p.add_argument(
        "--detect-only",
        action="store_true",
        help=_("print detected build system and exit"),
    )


def run(args: argparse.Namespace) -> int:
    root = Path(args.chdir).expanduser().resolve() if args.chdir else Path.cwd().resolve()
    if not root.is_dir():
        raise SystemExit(f"zfr build: not a directory: {root}")

    if args.detect_only:
        info = detect_build_system(root)
        if info is None:
            print("unknown")
            return 1
        print(info.name)
        return 0

    builddir = Path(args.builddir).expanduser() if args.builddir else None
    if builddir is not None and not builddir.is_absolute():
        builddir = root / builddir
    build_project(
        root,
        builddir=builddir,
        dry_run=args.dry_run,
        verbose=args.verbose,
        jobs=resolve_jobs(getattr(args, "jobs", None)),
    )
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
