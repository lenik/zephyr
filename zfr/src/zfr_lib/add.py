
# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr add — instantiate puff(s) from the language template."""

from __future__ import annotations

import argparse
from pathlib import Path

from .cli import register_command
from .i18n import _
from .puff import _add_one, _normalize_names

def cmd_add(names: str | list[str], workdir: Path | None = None) -> None:
    for name in _normalize_names(names):
        _add_one(name, workdir=workdir)


NAME = "add"
HELP = _('instantiate puff(s) from the language template')
DESCRIPTION = _('Detect language and add puff(s) from pkgdatadir/<lang>.')


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("puff_names", nargs="+", help=_("new puff name(s) (snake_case recommended)"))


def run(args: argparse.Namespace) -> int:
    cmd_add(list(args.puff_names))
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
