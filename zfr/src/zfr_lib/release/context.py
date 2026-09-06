# SPDX-License-Identifier: AGPL-3.0-or-later
"""Building context shared by gh-makerelease steps."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .logutil import quit


@dataclass
class Options:
    force: bool = False
    local: bool = False
    upload: bool = False
    docker: bool = False
    dput_host: str = ""
    base_image: str = "b4f-debian:trixie"
    docker_server: str = ""
    no_install: bool = False
    no_tag: bool = False
    no_upload: bool = False
    no_release: bool = False
    no_publish: bool = False
    no_rpm: bool = False
    no_deb: bool = False
    chdir: str = ""
    dpkg_buildopts: list[str] = field(default_factory=list)
    jobs: int = 0


@dataclass
class Context:
    projectdir: Path
    project_type: str = ""
    version: str = ""
    pkgname: str = ""
    tag: str = ""
    builddir: Path | None = None
    tarball: str = ""
    notes: str = ""
    changes_file: str = ""
    deb_files: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    opts: Options = field(default_factory=Options)


def ctx_reset_artifacts(ctx: Context) -> None:
    ctx.deb_files = []
    ctx.attachments = []
    ctx.tarball = ""
    ctx.notes = ""
    ctx.changes_file = ""


def ctx_init(opts: Options | None = None) -> Context:
    """Resolve project directory and clear artifact slots. Type/version filled later."""
    opts = opts or Options()
    if opts.chdir:
        projectdir = Path(opts.chdir).expanduser().resolve()
    else:
        projectdir = Path.cwd().resolve()

    if not projectdir.is_dir():
        quit(f"Not a directory: {projectdir}")

    try:
        subprocess.check_output(
            ["git", "-C", str(projectdir), "rev-parse", "--git-dir"],
            text=True,
        )
    except subprocess.CalledProcessError:
        quit(f"Not inside a git repository: {projectdir}")

    try:
        os.chdir(projectdir)
    except OSError:
        quit(f"Could not cd to project directory {projectdir}.")
    ctx = Context(projectdir=projectdir, opts=opts)
    ctx_reset_artifacts(ctx)
    return ctx
