# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr release / zfr-release — tag, build, package, install, private upload.

Pipeline: detect → tag/push → build/package → local deb install → deb/rpm
upload (dput / private cloud) → optional ``gh release create``.

Marketplace publish (npm / VSIX) is **not** included — use ``zfr publish``.
"""

from __future__ import annotations

import argparse

from ..cli import register_command
from ..i18n import _
from ..jobs import add_job_argument, resolve_jobs
from .context import Options
from .logutil import set_log_level
from .pipeline import run_release
from .util import load_default_options

_DEFAULT_BASE_IMAGE = "b4f-debian:trixie"

NAME = "release"
HELP = _("tag, build, package, install, and upload (private cloud)")
DESCRIPTION = _(
    "Detect project type, tag and push, build/package, optionally install "
    "local debs, upload deb/rpm to the private pool, and create a GitHub "
    "release. Does not publish to npm/VSIX marketplaces (see zfr publish). "
    "Also available as the zfr-release wrapper."
)


def add_release_arguments(p: argparse.ArgumentParser) -> None:
    """Attach release / publish shared options."""
    add_job_argument(p)
    p.add_argument(
        "-C",
        "--chdir",
        metavar="DIR",
        default="",
        help=_("change to DIR before detecting the project"),
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
        help=_("Build in local, no tag/push/GitHub release (implies -U)"),
    )
    p.add_argument(
        "-t",
        "--test",
        action="store_true",
        help=_("Alias for -l -I (local build, skip install)"),
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
        help=_("Skip dput / private-cloud upload (-u reuses build artifacts)"),
    )
    p.add_argument(
        "-R",
        "--no-release",
        action="store_true",
        help=_("Skip GitHub release"),
    )
    p.add_argument(
        "-Y",
        "--no-rpm",
        action="store_true",
        help=_("Skip RPM build (packaging/rpm/Makefile)"),
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


add_arguments = add_release_arguments


def apply_release_implications(ns: argparse.Namespace) -> None:
    """Apply -t → -l -I and -l → -U (mutates *ns* in place)."""
    if getattr(ns, "test", False):
        ns.local = True
        ns.no_install = True
    if ns.local:
        ns.no_upload = True


def namespace_to_options(ns: argparse.Namespace) -> Options:
    """Convert a parsed argparse namespace into release Options."""
    apply_release_implications(ns)
    dpkg_buildopts: list[str] = []
    if ns.build_binary:
        dpkg_buildopts.append("-b")
    if ns.unsigned:
        dpkg_buildopts.extend(["-us", "-uc"])
    if ns.no_pre_clean:
        dpkg_buildopts.append("-nc")
    docker = bool(ns.docker or ns.docker_server)
    return Options(
        force=bool(ns.force),
        local=bool(ns.local),
        upload=bool(ns.upload),
        docker=docker,
        dput_host=ns.dput_host or "",
        base_image=ns.base_image or _DEFAULT_BASE_IMAGE,
        docker_server=ns.docker_server or "",
        no_install=bool(ns.no_install),
        no_tag=bool(ns.no_tag),
        no_upload=bool(ns.no_upload),
        no_release=bool(ns.no_release),
        no_publish=False,
        no_rpm=bool(ns.no_rpm),
        no_deb=bool(ns.no_deb),
        chdir=ns.chdir or "",
        dpkg_buildopts=dpkg_buildopts,
        jobs=resolve_jobs(getattr(ns, "jobs", None)),
    )


def parse_release_args(
    argv: list[str] | None = None,
    *,
    prog: str | None = None,
) -> argparse.Namespace:
    """Parse argv with defaults from ``zfr-release.options`` (CLI wins)."""
    defaults = load_default_options()
    args_in = list(argv) if argv is not None else None
    if args_in is None:
        import sys

        args_in = sys.argv[1:]
    combined = defaults + args_in
    p = argparse.ArgumentParser(prog=prog or "zfr-release", description=DESCRIPTION)
    add_release_arguments(p)
    return p.parse_args(combined)


def cmd_release(ns: argparse.Namespace) -> int:
    """Run the native release pipeline from a parsed namespace."""
    set_log_level(1 + int(ns.verbose or 0) - int(ns.quiet or 0))
    return run_release(namespace_to_options(ns))


def run(args: argparse.Namespace) -> int:
    return cmd_release(args)


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
