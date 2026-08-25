
# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr ize — bring an existing project up to current zephyr style."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import _is_zfr_meta_repo, find_project_dir
from ..cli import register_command
from ..i18n import _
from ..lang import LANGS
from .engine import Ize
from .util import _role

def cmd_ize(
    *,
    lang: str | None = None,
    dry_run: bool = False,
    man: bool = True,
    subst: bool = True,
    mesonize: bool = True,
    commit: bool = False,
    author: str | None = None,
    verbose: bool = False,
    color: str = "auto",
    workdir: Path | None = None,
) -> int:
    if commit and dry_run:
        raise SystemExit("zfr ize: --commit cannot be combined with --dry-run")
    root = find_project_dir(workdir)
    if _is_zfr_meta_repo(root):
        raise SystemExit(
            f"{root} looks like the zephyr meta-repo. "
            "Run zfr ize from a language project, not the repository root."
        )
    role = _role(root)
    if lang:
        if lang not in LANGS:
            raise SystemExit(f"unknown language {lang!r} (one of: {', '.join(LANGS)})")
        detected = lang
    else:
        from .. import detect_lang

        try:
            detected = detect_lang(root)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            print("pass -l LANG to ize a project whose language could not be detected", file=sys.stderr)
            return 2
    if role == "meta":
        raise SystemExit("zfr ize does not operate on the meta-repo root")
    Ize(
        root,
        lang=detected,
        dry_run=dry_run,
        do_man=man,
        do_subst=subst,
        do_mesonize=mesonize,
        do_commit=commit,
        author=author,
        verbose=verbose,
        color=color,
    ).run()
    return 0


NAME = "ize"
HELP = _('refactor this project to current zephyr style')
DESCRIPTION = _('Refactor the current project to match current zephyr style: missing debian/rpm files, meson targets, AsciiDoc man pages, and Meson version substitutions. Walks from cwd toward parents.')


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("-l", "--lang", metavar="LANG", help=_("language template to align with (default: detect; one of: %s)") % ", ".join(LANGS))
    p.add_argument("-n", "--dry-run", action="store_true", help=_("print planned changes without writing files"))
    p.add_argument(
        "-c",
        "--commit",
        action="store_true",
        help=_(
            "bump patch version (debian/changelog + VERSION), git add -A, "
            "and commit ize changes with a verbose message"
        ),
    )
    p.add_argument(
        "-a",
        "--author",
        metavar="AUTHOR",
        help=_(
            "changelog author for --commit (Name or 'Name <email>'); "
            "default: reuse the previous debian/changelog trailer"
        ),
    )
    p.add_argument("-v", "--verbose", action="store_true", help=_("also print skipped files"))
    p.add_argument(
        "-m",
        "--mesonize",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=_("run 2meson to convert Autotools/CMake to Meson when present (default: on)"),
    )
    p.add_argument("--no-man", action="store_true", help=_("do not convert groff .1 man pages to docs/*.adoc"))
    p.add_argument("--no-subst", action="store_true", help=_("do not turn hardcoded versions into @VERSION@ / config.h"))
    p.add_argument("--color", choices=("auto", "always", "never"), default="auto", help=_("CSR (console SGR) highlighting (default: auto)"))


def run(args: argparse.Namespace) -> int:
    return cmd_ize(
        lang=args.lang,
        dry_run=args.dry_run,
        man=not args.no_man,
        subst=not args.no_subst,
        mesonize=args.mesonize,
        commit=args.commit,
        author=args.author,
        verbose=args.verbose,
        color=args.color,
    )


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
