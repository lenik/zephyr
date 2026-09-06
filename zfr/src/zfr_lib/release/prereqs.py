# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prerequisite checks for the detected project type."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..packaging_host import can_build_local, find_build_host_file
from ..pkg.kinds import detect_packaging_kinds
from .context import Context
from .detect import has_rpm_makefile
from .logutil import log1, quit


def check_prereqs(
    projectdir: Path | str,
    project_type: str,
    *,
    need_gh: bool = True,
) -> None:
    projectdir = Path(projectdir)
    log1("Checking prerequisites...")
    log1("  inside git repo")
    log1(f"  Project type detected: {project_type}")

    if project_type == "debian":
        n_tool = 0
        if shutil.which("debuild"):
            log1("  debuild available")
            n_tool += 1
        if shutil.which("dpkg-buildpackage"):
            log1("  dpkg-buildpackage available")
            n_tool += 1
        if n_tool == 0:
            quit("debuild or dpkg-buildpackage not found.")
    elif project_type in ("vsix", "nodejs"):
        if shutil.which("pnpm"):
            log1("  pnpm available")
        else:
            quit("pnpm not found.")

    kinds = detect_packaging_kinds(projectdir)
    if has_rpm_makefile(projectdir) or any(k.name != "deb" for k in kinds):
        if shutil.which("make"):
            log1("  make available (packaging/)")
        elif any(k.name not in {"deb", "npm", "vsix"} for k in kinds):
            quit("make not found (required for packaging/).")

    if has_rpm_makefile(projectdir):
        if can_build_local("rpm"):
            log1("  rpmbuild available")
        elif find_build_host_file(projectdir, "rpm") is not None:
            log1("  rpm .build-host available (remote)")
        else:
            log1("  warning: rpmbuild/.build-host missing — RPM packaging will be skipped")

    if not need_gh:
        log1("  skipping gh checks (local / no remote release steps)")
        return

    if shutil.which("gh"):
        log1("  gh CLI available")
    else:
        quit("gh CLI not found.")

    auth = subprocess.run(
        ["gh", "auth", "status", "-h", "github.com"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if auth.returncode == 0:
        log1("  gh authenticated")
    else:
        quit("gh not authenticated.")


def step_prereqs(ctx: Context) -> None:
    opts = ctx.opts
    need_gh = not (
        opts.local
        or (opts.no_tag and opts.no_release)
    )
    check_prereqs(ctx.projectdir, ctx.project_type, need_gh=need_gh)
