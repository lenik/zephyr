# SPDX-License-Identifier: AGPL-3.0-or-later
"""Debian packager implementation."""

from __future__ import annotations

import shutil

from cmd_run import merge_env, run_cmd
from jobs import deb_build_options_parallel, debuild_jobs_args
from pkg_docker import build4_debian, build4_debian_remote
from .provider import PackagerContext


class DebPackager:
    name = "deb"

    def skip_reason(self, ctx: PackagerContext) -> str | None:
        del ctx
        return None

    def build(self, ctx: PackagerContext) -> bool:
        opts = list(ctx.dpkg_buildopts)
        jobs = ctx.jobs
        if ctx.docker or ctx.docker_server:
            if ctx.docker_server:
                build4_debian_remote(
                    ctx.root,
                    docker_server=ctx.docker_server,
                    base_image=ctx.base_image,
                    dpkg_buildopts=opts,
                    jobs=jobs,
                    dry_run=ctx.dry_run,
                )
            else:
                build4_debian(
                    ctx.root,
                    base_image=ctx.base_image,
                    dpkg_buildopts=opts,
                    jobs=jobs,
                    dry_run=ctx.dry_run,
                )
            return True
        env = merge_env()
        parallel = deb_build_options_parallel(
            jobs, prev=env.get("DEB_BUILD_OPTIONS", "")
        )
        if parallel is not None:
            env["DEB_BUILD_OPTIONS"] = parallel
        jargs = debuild_jobs_args(jobs)
        if shutil.which("debuild"):
            cmd = ["debuild", *jargs, *opts]
        else:
            cmd = ["dpkg-buildpackage", *jargs, *opts]
        run_cmd(cmd, cwd=ctx.root, env=env, dry_run=ctx.dry_run)
        return True


def package_deb(
    root,
    *,
    dpkg_buildopts: list[str] | None = None,
    docker: bool = False,
    docker_server: str = "",
    base_image: str = "b4f-debian:trixie",
    jobs: int | None = None,
    dry_run: bool = False,
) -> None:
    """Backward-compatible function wrapper around :class:`DebPackager`."""
    from pathlib import Path

    DebPackager().build(
        PackagerContext(
            root=Path(root),
            jobs=jobs,
            dry_run=dry_run,
            dpkg_buildopts=list(dpkg_buildopts or []),
            docker=docker,
            docker_server=docker_server,
            base_image=base_image,
        )
    )
