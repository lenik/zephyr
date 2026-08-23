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

def cmd_rename(project_name: str, examples: list[str], workdir: Path | None = None) -> None:
    root = (workdir or Path.cwd()).resolve()
    print(f"rename zephyr → {project_name}")
    pairs = replacement_pairs("zephyr", project_name)
    files, renames = rewrite_tree(root, pairs, rename_paths=True)
    print(f"  project: {files} file(s) rewritten, {renames} path(s) renamed")

    for ex in examples:
        print(f"rename example {TEMPLATE_PUFF} → {ex}")
        pairs = replacement_pairs(TEMPLATE_PUFF, ex)
        files, renames = rewrite_tree(root, pairs, rename_paths=True)
        print(f"  example: {files} file(s) rewritten, {renames} path(s) renamed")


NAME = "rename"
HELP = _('rename zephyr project and example puff names')
DESCRIPTION = _('Rename zephyr → ProjectName and some_puff1 → example names.')


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("project_name", help=_("new project name (replaces 'zephyr')"))
    p.add_argument("puff_names", nargs="*", help=_("new example names (each replaces template some_puff1)"))


def run(args: argparse.Namespace) -> int:
    cmd_rename(args.project_name, list(args.puff_names))
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
