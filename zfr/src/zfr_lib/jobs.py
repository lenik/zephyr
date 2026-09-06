# SPDX-License-Identifier: AGPL-3.0-or-later
"""Parallel job count helpers for build/package/release."""

from __future__ import annotations

import argparse
import os

from .i18n import _


def default_job_count() -> int:
    """Return a positive parallel job count (CPU cores, at least 1)."""
    n = os.cpu_count()
    return max(1, int(n or 1))


def add_job_argument(p: argparse.ArgumentParser) -> None:
    """Add ``-j`` / ``--job N`` (default: number of CPU cores)."""
    n = default_job_count()
    p.add_argument(
        "-j",
        "--job",
        metavar="N",
        type=int,
        default=n,
        dest="jobs",
        help=_("parallel jobs / concurrent packagers (default: %s CPU cores)") % n,
    )


def resolve_jobs(value: int | None) -> int:
    """Normalize a jobs value; treat None/non-positive as the core default."""
    if value is None or value <= 0:
        return default_job_count()
    return int(value)
