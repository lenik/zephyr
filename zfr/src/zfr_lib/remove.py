
# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr remove — drop puff(s) from the current project."""

from __future__ import annotations

import argparse
from pathlib import Path

from .cli import register_command
from .i18n import _
from .puff import _normalize_names, _remove_one

def cmd_remove(names: str | list[str], workdir: Path | None = None) -> None:
    for name in _normalize_names(names):
        _remove_one(name, workdir=workdir)


NAME = "remove"
HELP = _('remove puff(s) from the current project')
DESCRIPTION = _('Remove puff files for NAME(s) from the current project.')


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("puff_names", nargs="+", help=_("puff name(s) to remove"))


def run(args: argparse.Namespace) -> int:
    cmd_remove(list(args.puff_names))
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
