# SPDX-License-Identifier: AGPL-3.0-or-later
"""Logging helpers for the release pipeline (ported from gh-utils)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import NoReturn

_log_level = 1


def quiet() -> None:
    global _log_level
    _log_level -= 1


def verbose() -> None:
    global _log_level
    _log_level += 1


def get_log_level() -> int:
    return _log_level


def set_log_level(level: int) -> None:
    global _log_level
    _log_level = level


def log0(msg: str) -> None:
    if _log_level >= 0:
        print(msg, file=sys.stderr)


def log1(msg: str) -> None:
    if _log_level >= 1:
        print(msg, file=sys.stderr)


def log2(msg: str) -> None:
    if _log_level >= 2:
        print(msg, file=sys.stderr)


def quit(msg: str) -> NoReturn:
    """Print *msg* to stderr and exit with status 1."""
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def run(*argv: str | Path) -> None:
    """Print ``  cmd`` then run *argv* with ``check=True``."""
    cmd = [str(a) for a in argv]
    print(" ", " ".join(cmd))
    subprocess.run(cmd, check=True)
