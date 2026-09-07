# SPDX-License-Identifier: AGPL-3.0-or-later
"""Argparse helpers shared by `zfr` and the `zfr-*` wrappers."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from typing import Any

from .i18n import init_i18n

AddArguments = Callable[[argparse.ArgumentParser], None]
RunFn = Callable[[argparse.Namespace], int | None]


class SubcommandHelpFormatter(argparse.HelpFormatter):
    """Usage shows ``COMMAND``; help lists subcommands without a brace blob."""

    def _format_action(self, action: argparse.Action) -> str:
        if isinstance(action, argparse._SubParsersAction):
            parts: list[str] = []
            for sub in self._iter_indented_subactions(action):
                parts.append(super()._format_action(sub))
            return "".join(parts)
        return super()._format_action(action)


def standalone_main(
    prog: str,
    description: str,
    add_arguments: AddArguments,
    run: RunFn,
    argv: Sequence[str] | None = None,
) -> int:
    """Build a one-command parser (for `zfr-lint`, `zfr-create`, …)."""
    init_i18n()
    parser = argparse.ArgumentParser(prog=prog, description=description)
    add_arguments(parser)
    args = parser.parse_args(None if argv is None else list(argv))
    try:
        result = run(args)
    except BrokenPipeError:
        return 0
    return 0 if result is None else int(result)


def register_command(
    sub: Any,
    name: str,
    *,
    help: str,
    description: str,
    add_arguments: AddArguments,
    run: RunFn,
) -> argparse.ArgumentParser:
    parser = sub.add_parser(name, help=help, description=description)
    add_arguments(parser)
    parser.set_defaults(_run=run)
    return parser
