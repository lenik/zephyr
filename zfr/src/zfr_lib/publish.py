# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr publish / zfr-publish — release plus marketplace publish.

Runs the same pipeline as ``zfr release``, then publishes to public
marketplaces when defined (currently npm and VSIX).
"""

from __future__ import annotations

import argparse

from .cli import register_command
from .i18n import _
from .release import (
    DESCRIPTION as _RELEASE_DESCRIPTION,
    add_release_arguments,
    namespace_to_options,
)
from .release.logutil import set_log_level
from .release.pipeline import run_publish

NAME = "publish"
HELP = _("release then publish to marketplaces (npm / VSIX)")
DESCRIPTION = _(
    "Run the full zfr release pipeline, then publish to public marketplaces "
    "when defined for this project (currently npm and VSIX). "
    "Also available as the zfr-publish wrapper."
)


def add_arguments(p: argparse.ArgumentParser) -> None:
    """Same options as ``zfr release``."""
    add_release_arguments(p)


def run(args: argparse.Namespace) -> int:
    set_log_level(1 + int(args.verbose or 0) - int(args.quiet or 0))
    return run_publish(namespace_to_options(args))


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )


# Re-export for tests / docs that mention release description alongside publish.
RELEASE_DESCRIPTION = _RELEASE_DESCRIPTION
