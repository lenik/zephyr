# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr package — detect packaging type and build packages."""

from __future__ import annotations

import argparse
from pathlib import Path

from .cli import register_command
from .i18n import _
from .jobs import add_job_argument, resolve_jobs
from .pkg import detect_packaging_kinds, package_project

NAME = "package"
HELP = _("detect packaging type and build packages")
DESCRIPTION = _(
    "Detect packaging types (deb, rpm, npm/vsix, mingw, …) and build them "
    "sequentially (deb, then rpm, …). -j/--job is per-packager build "
    "parallelism (debuild/make -j), not concurrent packagers. Each "
    "packager's stdout/stderr is captured with fdmux into an FDM file; live "
    "status lines show progress. On failure, browse with `zfr lasterror`. "
    "Upload is on by default (-u); use -U/--no-upload to skip."
)

_DEFAULT_BASE_IMAGE = "b4f-debian:trixie"


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-C",
        "--chdir",
        metavar="DIR",
        default="",
        help=_("change to DIR before detecting packaging"),
    )
    add_job_argument(p)
    upload = p.add_mutually_exclusive_group()
    upload.add_argument(
        "-u",
        "--upload",
        dest="upload",
        action="store_true",
        help=_("upload packages after build (default)"),
    )
    upload.add_argument(
        "-U",
        "--no-upload",
        dest="upload",
        action="store_false",
        help=_("do not upload (skip dput / registry publish)"),
    )
    p.set_defaults(upload=True)
    p.add_argument(
        "-p",
        "--dput-host",
        metavar="HOST",
        default="",
        help=_("dput upload host for .changes (debian)"),
    )
    p.add_argument(
        "-D",
        "--no-deb",
        action="store_true",
        help=_("skip Debian debuild"),
    )
    p.add_argument(
        "-Y",
        "--no-rpm",
        action="store_true",
        help=_("skip RPM packaging/rpm Makefile"),
    )
    p.add_argument(
        "--only",
        metavar="KIND",
        action="append",
        default=[],
        help=_("only build KIND (deb, rpm, npm, mingw, …); repeatable"),
    )
    p.add_argument(
        "-b",
        "--build-binary",
        action="store_true",
        help=_("Debian binary-only build (no .dsc)"),
    )
    p.add_argument(
        "-n",
        "--no-pre-clean",
        action="store_true",
        help=_("Debian: reuse build cache (dpkg -nc)"),
    )
    p.add_argument(
        "--unsigned",
        action="store_true",
        help=_("Debian: build unsigned packages"),
    )
    p.add_argument(
        "-d",
        "--docker",
        action="store_true",
        help=_("build debian package with build4 (Docker)"),
    )
    p.add_argument(
        "-B",
        "--base-image",
        metavar="IMAGE",
        default=_DEFAULT_BASE_IMAGE,
        help=_("build4 target image (default: %s)") % _DEFAULT_BASE_IMAGE,
    )
    p.add_argument(
        "-s",
        "--docker-server",
        metavar="SERVER",
        default="",
        help=_("run build4 over SSH on SERVER (implies -d)"),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=_("print planned commands without running them"),
    )
    p.add_argument(
        "--detect-only",
        action="store_true",
        help=_("print detected packaging kinds and exit"),
    )


def _dpkg_opts(args: argparse.Namespace) -> list[str]:
    opts: list[str] = []
    if args.build_binary:
        opts.append("-b")
    if args.no_pre_clean:
        opts.append("-nc")
    if args.unsigned:
        opts.extend(["-us", "-uc"])
    return opts


def run(args: argparse.Namespace) -> int:
    root = Path(args.chdir).expanduser().resolve() if args.chdir else Path.cwd().resolve()
    if not root.is_dir():
        raise SystemExit(f"zfr package: not a directory: {root}")

    if args.detect_only:
        kinds = detect_packaging_kinds(root)
        if not kinds:
            print("none")
            return 1
        for k in kinds:
            print(k.name)
        return 0

    docker = bool(args.docker or args.docker_server)
    package_project(
        root,
        upload=bool(args.upload),
        dput_host=args.dput_host or "",
        no_deb=bool(args.no_deb),
        no_rpm=bool(args.no_rpm),
        only=list(args.only or []),
        dpkg_buildopts=_dpkg_opts(args),
        docker=docker,
        docker_server=args.docker_server or "",
        base_image=args.base_image,
        dry_run=bool(args.dry_run),
        jobs=resolve_jobs(getattr(args, "jobs", None)),
    )
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
