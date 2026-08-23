# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr create / rename / add / remove command implementations."""

from __future__ import annotations

import re
import shutil
import subprocess
import uuid
from email.utils import formatdate
from pathlib import Path

from . import (
    LANGS,
    TEMPLATE_PUFF,
    append_meson_list_entry,
    apply_name_replacements,
    case_variants,
    copy_renamed_file,
    detect_lang,
    instantiation_pairs,
    is_probably_text,
    iter_files,
    pkgdatadir,
    project_version,
    relative_to,
    remove_meson_list_entry,
    replacement_pairs,
    rewrite_tree,
    template_dir,
)
import argparse
from .cli import register_command
from .i18n import _

def cmd_version(
    *,
    git: bool = False,
    changelog: bool = False,
    rpm: bool = False,
    workdir: Path | None = None,
) -> None:
    """Print the current project version (walks parents from cwd)."""
    if git and changelog:
        raise SystemExit("zfr version: use only one of --git and --changelog")
    source = "git" if git else "changelog" if changelog else None
    print(project_version(workdir, source=source, rpm=rpm), flush=True)


NAME = "version"
HELP = _('print current project version (walks parents from cwd)')
DESCRIPTION = _('Print the current project version (walks from cwd toward parent directories).')


def add_arguments(p: argparse.ArgumentParser) -> None:
    srcg = p.add_mutually_exclusive_group()
    srcg.add_argument("-g", "--git", action="store_true", help=_("use git describe (default when git and .git are available)"))
    srcg.add_argument("-c", "--changelog", action="store_true", help=_("use debian/changelog (default when git or .git is unavailable)"))
    p.add_argument("-r", "--rpm", action="store_true", help=_("print an RPM-compatible Version (hyphens mapped to underscores)"))


def run(args: argparse.Namespace) -> int:
    cmd_version(git=args.git, changelog=args.changelog, rpm=args.rpm)
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
