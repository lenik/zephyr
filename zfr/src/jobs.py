# SPDX-License-Identifier: AGPL-3.0-or-later
"""Parallel job count helpers for build/package/release."""

from __future__ import annotations

import argparse
import os

from i18n import _


def default_job_count() -> int:
    """Return a positive parallel job count (CPU cores, at least 1)."""
    n = os.cpu_count()
    return max(1, int(n or 1))


def add_job_argument(p: argparse.ArgumentParser) -> None:
    """Add ``-j`` / ``--job [N]`` (default/bare: auto — debuild ``-j``)."""
    p.add_argument(
        "-j",
        "--job",
        metavar="N",
        nargs="?",
        const=None,
        type=int,
        default=None,
        dest="jobs",
        help=_(
            "job budget: omit or pass -j alone for auto "
            "(debuild/dpkg-buildpackage get bare -j); "
            "-j N pins a total budget split across concurrent planned workers"
        ),
    )


def jobs_is_auto(value: int | None) -> bool:
    """True when the caller did not pin an explicit positive job count."""
    return value is None or int(value) <= 0


def resolve_jobs(value: int | None) -> int:
    """Normalize a jobs value; treat None/non-positive as the core default.

    Use for build systems that need a concrete ``-jN`` (make, meson, …).
    For debuild, prefer :func:`debuild_jobs_args` so auto stays bare ``-j``.
    """
    if jobs_is_auto(value):
        return default_job_count()
    return int(value)


def split_job_budget(total: int | None, n_workers: int) -> list[int | None]:
    """Split a job budget across *n_workers* concurrent planned workers.

    Auto (``None`` / ≤0): every worker stays auto (``None``) — debuild keeps
    bare ``-j``; make/other resolve locally.

    Explicit ``N``: divide ``N`` as evenly as possible (each share at least 1).
    Sequential plans use ``n_workers=1`` so the single worker receives full ``N``.
    """
    n = max(1, int(n_workers))
    if jobs_is_auto(total):
        return [None] * n
    budget = max(1, int(total))
    base, rem = divmod(budget, n)
    out: list[int | None] = []
    for i in range(n):
        share = base + (1 if i < rem else 0)
        out.append(max(1, share))
    return out


def debuild_jobs_args(value: int | None) -> list[str]:
    """Return debuild/dpkg-buildpackage ``-j`` argv fragment.

    Auto (default): bare ``-j`` so dpkg can choose parallelism.
    Explicit: ``-jN``.
    """
    if jobs_is_auto(value):
        return ["-j"]
    return [f"-j{int(value)}"]


def deb_build_options_parallel(value: int | None, *, prev: str = "") -> str | None:
    """``DEB_BUILD_OPTIONS`` parallel fragment, or None when auto (let ``-j`` win)."""
    if jobs_is_auto(value):
        return None
    parallel = f"parallel={int(value)}"
    prev = (prev or "").strip()
    return f"{prev} {parallel}".strip() if prev else parallel
