# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr detect — print the detected language for the current tree."""

from __future__ import annotations

import argparse
import sys

from . import detect_lang, pkgdatadir
from .cli import register_command
from .i18n import _
from .shape import resolve_layout, shape_score

NAME = "detect"
HELP = _("print detected language for the current directory")
DESCRIPTION = _("Print the detected language of the current project and layout details on stderr.")


def add_arguments(p: argparse.ArgumentParser) -> None:
    return


def run(args: argparse.Namespace) -> int:
    layout = resolve_layout()
    lang = detect_lang(layout.packagedir)
    print(lang, flush=True)
    print(
        f"packagedir: {layout.packagedir}\n"
        f"repodir: {layout.repodir}\n"
        f"role: {layout.role}\n"
        f"shape: {shape_score(layout.packagedir)}\n"
        f"pkgdatadir: {pkgdatadir()}",
        file=sys.stderr,
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
