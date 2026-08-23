# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr release — parse gh-makerelease options and exec gh-makerelease.

This command does not implement tagging, packaging, or GitHub uploads.
It only validates the same option grammar as gh-makerelease, rebuilds
an argv, and execs ``gh-makerelease`` from PATH.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from .i18n import _

_DEFAULT_BASE_IMAGE = "b4f-debian:trixie"


def add_release_arguments(p: argparse.ArgumentParser) -> None:
    """Attach gh-makerelease options (parsed here, implemented there)."""
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
        help=_("Reuse build cache"),
    )
    p.add_argument(
        "-u",
        "--upload",
        action="store_true",
        help=_("Reuse existing artifacts; build only if missing"),
    )
    p.add_argument(
        "--unsigned",
        action="store_true",
        help=_("Build unsigned packages"),
    )
    p.add_argument(
        "-p",
        "--dput-host",
        metavar="HOST",
        default="",
        help=_("dput upload host for .changes (debian)"),
    )
    p.add_argument(
        "-d",
        "--docker",
        action="store_true",
        help=_("Build debian package with build4 (Docker)"),
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
        help=_("Run build4 over SSH on SERVER (implies -d)"),
    )
    p.add_argument(
        "-l",
        "--local",
        action="store_true",
        help=_("Build in local, no tag/push/release"),
    )
    p.add_argument(
        "-f",
        "--force",
        action="store_true",
        help=_("Replace existing release and tag if present"),
    )
    p.add_argument(
        "-I",
        "--no-install",
        action="store_true",
        help=_("Skip sudo dpkg -i (still find debs/changes)"),
    )
    p.add_argument(
        "-T",
        "--no-tag",
        action="store_true",
        help=_("Skip git tag create/push"),
    )
    p.add_argument(
        "-U",
        "--no-upload",
        action="store_true",
        help=_("Skip dput upload to deb pool (-u reuses build artifacts)"),
    )
    p.add_argument(
        "-R",
        "--no-release",
        action="store_true",
        help=_("Skip GitHub release"),
    )
    p.add_argument(
        "-P",
        "--no-publish",
        action="store_true",
        help=_("Skip VSIX marketplace publish"),
    )
    p.add_argument(
        "-Y",
        "--no-rpm",
        action="store_true",
        help=_("Skip RPM build (rpm/Makefile)"),
    )
    p.add_argument(
        "-D",
        "--no-deb",
        action="store_true",
        help=_("Skip Debian debuild"),
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=_("Verbose logging"),
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help=_("Less output"),
    )


def compose_makerelease_argv(ns: argparse.Namespace) -> list[str]:
    """Rebuild gh-makerelease argv from a parsed namespace (no defaults)."""
    argv: list[str] = []
    if ns.build_binary:
        argv.append("--build-binary")
    if ns.no_pre_clean:
        argv.append("--no-pre-clean")
    if ns.upload:
        argv.append("--upload")
    if ns.unsigned:
        argv.append("--unsigned")
    if ns.dput_host:
        argv.extend(["--dput-host", ns.dput_host])
    if ns.docker:
        argv.append("--docker")
    if ns.base_image and ns.base_image != _DEFAULT_BASE_IMAGE:
        argv.extend(["--base-image", ns.base_image])
    if ns.docker_server:
        argv.extend(["--docker-server", ns.docker_server])
    if ns.local:
        argv.append("--local")
    if ns.force:
        argv.append("--force")
    if ns.no_install:
        argv.append("--no-install")
    if ns.no_tag:
        argv.append("--no-tag")
    if ns.no_upload:
        argv.append("--no-upload")
    if ns.no_release:
        argv.append("--no-release")
    if ns.no_publish:
        argv.append("--no-publish")
    if ns.no_rpm:
        argv.append("--no-rpm")
    if ns.no_deb:
        argv.append("--no-deb")
    argv.extend(["--verbose"] * int(ns.verbose or 0))
    argv.extend(["--quiet"] * int(ns.quiet or 0))
    return argv


def exec_makerelease(argv: Sequence[str]) -> int:
    """Replace this process with gh-makerelease. Never returns on success."""
    exe = shutil.which("gh-makerelease")
    if not exe:
        print(
            "zfr release: gh-makerelease not found on PATH "
            "(install the gh-makerelease package)",
            file=sys.stderr,
        )
        return 127
    os.execv(exe, [exe, *argv])
    return 0


def cmd_release(ns: argparse.Namespace) -> int:
    """Parse-only front end: recompose options and exec gh-makerelease."""
    return exec_makerelease(compose_makerelease_argv(ns))
