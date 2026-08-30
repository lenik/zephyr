# SPDX-License-Identifier: AGPL-3.0-or-later
"""Registered zfr subcommands (one module per command)."""

from __future__ import annotations

from collections.abc import Sequence
from types import ModuleType

from . import (
    about,
    add,
    create,
    detect,
    dist,
    ize,
    lint,
    release,
    remove,
    rename,
    shape,
    version,
)
from .i18n import cmd as i18n
from . import translate

COMMANDS: Sequence[ModuleType] = (
    create,
    rename,
    add,
    remove,
    about,
    version,
    lint,
    shape,
    dist,
    release,
    ize,
    i18n,
    translate,
    detect,
)
