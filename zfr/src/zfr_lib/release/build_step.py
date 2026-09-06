# SPDX-License-Identifier: AGPL-3.0-or-later
"""Orchestrate project build/package via in-process zfr APIs."""

from __future__ import annotations

from ..buildsys import build_project
from ..jobs import resolve_jobs
from ..pkg import package_project
from .artifacts import have_build_artifacts
from .context import Context
from .logutil import log1, quit


def step_build(ctx: Context) -> None:
    """Compile and package, or reuse artifacts when ``-u`` finds them."""
    opts = ctx.opts
    need_build = True
    if opts.upload and have_build_artifacts(
        ctx.project_type,
        ctx.projectdir,
        ctx.version,
        ctx.pkgname,
        ctx.builddir,
    ):
        log1("Reusing existing build artifacts (--upload)")
        need_build = False

    if not need_build:
        return

    jobs = resolve_jobs(opts.jobs if opts.jobs and opts.jobs > 0 else None)
    try:
        log1(f"Building project (jobs={jobs})")
        build_project(
            ctx.projectdir,
            jobs=jobs,
            verbose=False,
        )
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — surface as release failure
        quit(f"Build failed: {exc}")

    do_upload = not (opts.local or opts.no_upload)
    docker = bool(opts.docker or opts.docker_server)
    try:
        log1(
            f"Packaging project (upload={'yes' if do_upload else 'no'}, "
            f"jobs={jobs})"
        )
        package_project(
            ctx.projectdir,
            upload=do_upload,
            dput_host=opts.dput_host or "",
            no_deb=bool(opts.no_deb),
            no_rpm=bool(opts.no_rpm),
            dpkg_buildopts=list(opts.dpkg_buildopts or []),
            docker=docker,
            docker_server=opts.docker_server or "",
            base_image=opts.base_image or "b4f-debian:trixie",
            jobs=jobs,
            interactive_errors=False,
        )
    except SystemExit as exc:
        if exc.code in (0, None):
            pass
        else:
            msg = (
                exc.code
                if isinstance(exc.code, str)
                else (str(exc) or f"Packaging failed (exit {exc.code})")
            )
            quit(
                f"{msg}. If rpmbuild reported unpackaged "
                "files (.mo or locale man pages), add matching globs to "
                "packaging/rpm/*.spec %files (or run `zfr ize` / `zfr lint`)."
            )
    except Exception as exc:  # noqa: BLE001
        quit(
            f"Packaging failed: {exc}. If rpmbuild reported unpackaged "
            "files (.mo or locale man pages), add matching globs to "
            "packaging/rpm/*.spec %files (or run `zfr ize` / `zfr lint`)."
        )
