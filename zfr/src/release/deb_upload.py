# SPDX-License-Identifier: AGPL-3.0-or-later
"""Install built .deb packages locally; pool upload is handled by zfr-package."""

from __future__ import annotations

from .logutil import log1, quit, run

from .artifacts import find_changes_file, find_deb_files
from .context import Context


def step_deb_upload(ctx: Context) -> None:
    if ctx.project_type != "debian":
        return

    opts = ctx.opts
    assert ctx.builddir is not None
    ctx.deb_files = find_deb_files(ctx.projectdir, ctx.builddir, ctx.version)
    if not ctx.deb_files:
        quit("No .deb files found.")
    log1(f"Debian files: {' '.join(ctx.deb_files)}")

    if not opts.no_install:
        run("sudo", "dpkg", "-i", *ctx.deb_files)

    ctx.changes_file = find_changes_file(
        ctx.projectdir, ctx.builddir, ctx.version
    )
    if not ctx.changes_file:
        quit("No .changes file found.")
    log1(f"Changes file: {ctx.changes_file}")

    # dput is performed by ``zfr-package -u`` during step_build.
    if opts.local or opts.no_upload:
        if opts.no_upload and not opts.local:
            log1("Skipping dput (--no-upload)")
        return
    log1("Skipping dput here (zfr-package handles upload when -u)")
