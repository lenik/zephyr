# SPDX-License-Identifier: AGPL-3.0-or-later
"""``zfr comments`` — print / delete lint.comments for AI follow-up work."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib import find_project_dir
from cli import register_command
from i18n import _
from lint.comments import (
    delete_comments,
    normalize_rule_key,
    render_comments_report,
)

NAME = "comments"
HELP = _("print or delete project/user lint.comments with an AI work hint")
DESCRIPTION = _(
    "Print lint suggestion comments from .config/zfr/lint.comments "
    "(project) and ~/.config/zfr/lint.comments (user), then an AI hint to "
    "apply the suggestions and delete the consumed comments files. "
    "Optional ZLxxxx arguments filter which sections to show. "
    "Typical prompt: “do zfr-comments work.”"
)


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "rules",
        nargs="*",
        metavar="ZLxxxx",
        help=_("only these rule ids (default: all)"),
    )
    p.add_argument(
        "-C",
        "--directory",
        type=Path,
        default=None,
        help=_("project directory (default: walk from cwd)"),
    )
    scope = p.add_mutually_exclusive_group()
    scope.add_argument(
        "-u",
        "--user",
        action="store_true",
        help=_("user comments only (~/.config/zfr/lint.comments)"),
    )
    scope.add_argument(
        "-p",
        "--project",
        action="store_true",
        help=_("project comments only (.config/zfr/lint.comments)"),
    )
    p.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help=_("delete matching comments (files or selected sections)"),
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help=_("omit the AI hint trailer"),
    )


def run(args: argparse.Namespace) -> int:
    root = find_project_dir(getattr(args, "directory", None))
    include_project = not getattr(args, "user", False)
    include_user = not getattr(args, "project", False)
    if getattr(args, "user", False):
        include_project, include_user = False, True
    elif getattr(args, "project", False):
        include_project, include_user = True, False

    rule_ids: set[str] | None = None
    raw_rules = list(getattr(args, "rules", None) or [])
    if raw_rules:
        rule_ids = {normalize_rule_key(r) for r in raw_rules}

    if getattr(args, "delete", False):
        touched = delete_comments(
            root,
            include_project=include_project,
            include_user=include_user,
            rule_ids=rule_ids,
        )
        if not touched:
            sys.stdout.write(_("No matching lint.comments to delete.") + "\n")
            return 0
        for path in touched:
            sys.stdout.write(_("Deleted: %s") % path + "\n")
        return 0

    text = render_comments_report(
        root,
        include_project=include_project,
        include_user=include_user,
        rule_ids=rule_ids,
    )
    if getattr(args, "quiet", False):
        lines = [ln for ln in text.splitlines() if not ln.startswith("AI hint:")]
        text = "\n".join(lines).rstrip() + "\n"
    sys.stdout.write(text)
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
