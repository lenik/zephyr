# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr create / rename / add / remove command implementations."""

from __future__ import annotations

import argparse

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
from .add import cmd_add
from .cli import register_command
from .i18n import _
from .puff import _leftover_template_lines
from .remove import cmd_remove

DEFAULT_DISTRIBUTION = "unstable"
DEFAULT_INIT_VERSION = "0.0.1"
DEFAULT_AUTHOR = "Lenik (谢继雷)"
DEFAULT_EMAIL = "lenik@bodz.net"

_COPY_IGNORE = shutil.ignore_patterns(
    ".cache",
    ".cursor",
    ".git",
    ".hg",
    ".svn",
    ".vscode",
    "__pycache__",
    "bin",
    "build",
    "cargo-target",
    "dist",
    "rpmbuild",
    "meson-info",
    "meson-logs",
    "meson-private",
    "node_modules",
    "obj",
    "target",
    "CLAUDE.md",
    "*.pyc",
    "debhelper-build-stamp",
    "*.substvars",
    "*.debhelper",
    "*.buildinfo",
)


def _copy_ignore(directory: str, names: list[str]) -> set[str]:
    ignored = set(_COPY_IGNORE(directory, names))
    if Path(directory).name == "debian":
        for n in names:
            if n in {
                "files",
                "debhelper-build-stamp",
                ".debhelper",
                "zephyr",
            } or n.endswith((".substvars", ".debhelper.log", ".buildinfo")):
                ignored.add(n)
    return ignored


def _clean_copied_debian(dest: Path) -> None:
    """Drop packaging leftovers copied from a previously built template tree."""
    debian = dest / "debian"
    if not debian.is_dir():
        return
    for p in list(debian.rglob("*")):
        if not p.is_file():
            continue
        name = p.name
        if name in {
            "files",
            "debhelper-build-stamp",
        } or name.endswith((".substvars", ".debhelper", ".debhelper.log", ".buildinfo")):
            p.unlink(missing_ok=True)
    for child in list(debian.iterdir()):
        if child.is_dir() and child.name in (".debhelper", "build", "zephyr"):
            shutil.rmtree(child, ignore_errors=True)


def _write_debian_changelog(
    dest: Path,
    *,
    package: str,
    version: str,
    distribution: str,
    author: str,
    email: str,
) -> None:
    """Write a fresh debian/changelog (template changelog is omitted on create)."""
    deb_dir = dest / "debian"
    deb_dir.mkdir(parents=True, exist_ok=True)
    stamp = formatdate(localtime=True)
    text = (
        f"{package} ({version}) {distribution}; urgency=medium\n"
        f"\n"
        f"  * Initial release\n"
        f"\n"
        f" -- {author} <{email}>  {stamp}\n"
    )
    (deb_dir / "changelog").write_text(text, encoding="utf-8")
    (dest / "VERSION").write_text(f"{version.lstrip('v')}\n", encoding="utf-8")


def _githooks_pre_commit_src() -> Path | None:
    """Canonical pre-commit hook: installed pkgdatadir/githooks, else source tree."""
    candidates = [
        pkgdatadir() / "githooks" / "pre-commit",
        pkgdatadir() / ".githooks" / "pre-commit",
    ]
    here = Path(__file__).resolve()
    if here.parent.name == "zfr_lib":
        zfr_root = here.parents[2]
        repo = zfr_root.parent
        candidates.extend(
            [
                zfr_root / "githooks" / "pre-commit",
                zfr_root / ".githooks" / "pre-commit",
                repo / ".githooks" / "pre-commit",
                repo / "bash" / ".githooks" / "pre-commit",
            ]
        )
    for path in candidates:
        if path.is_file():
            return path
    return None


def _install_githooks(dest: Path) -> None:
    """Copy .githooks/pre-commit into *dest* (chmod +x) if a source hook exists."""
    src = _githooks_pre_commit_src()
    hook_dir = dest / ".githooks"
    dest_hook = hook_dir / "pre-commit"
    if src is None:
        if dest_hook.is_file():
            dest_hook.chmod(dest_hook.stat().st_mode | 0o111)
        return
    hook_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_hook)
    dest_hook.chmod(dest_hook.stat().st_mode | 0o111)


def _git_init_commit_tag(
    dest: Path,
    *,
    version: str,
    author: str,
    email: str,
) -> None:
    """Initialize git, create the first commit, and tag vVERSION."""
    def run(args: list[str]) -> None:
        subprocess.run(args, cwd=dest, check=True, capture_output=True, text=True)

    # Author identity via -c only (do not write user.name in git config).
    # core.hooksPath is local to this repo so .githooks/pre-commit runs.
    ident = ["-c", f"user.name={author}", "-c", f"user.email={email}"]

    run(["git", "init"])
    run(["git", "config", "core.hooksPath", ".githooks"])
    run(["git", "add", "-A"])
    ver = version.lstrip("v")
    msg = f"Initial release {ver}\n"
    run(["git", *ident, "commit", "-m", msg])
    tag = f"v{ver}"
    run(["git", *ident, "tag", "-a", tag, "-m", f"{tag}: initial release"])


def cmd_create(
    project_name: str,
    lang: str = "python",
    puff_names: list[str] | None = None,
    workdir: Path | None = None,
    *,
    distribution: str = DEFAULT_DISTRIBUTION,
    init_version: str = DEFAULT_INIT_VERSION,
    author: str = DEFAULT_AUTHOR,
    email: str = DEFAULT_EMAIL,
) -> None:
    """Copy a language template into ./<project_name>/ and rename the project."""
    root = (workdir or Path.cwd()).resolve()
    dest_arg = Path(project_name)
    # Allow absolute or nested paths; package/rename id is always the final component.
    dest = dest_arg if dest_arg.is_absolute() else (root / dest_arg)
    package = dest.name
    if not package or package in (".", ".."):
        raise SystemExit(f"invalid project path: {project_name!r}")
    if dest.exists():
        raise SystemExit(f"destination already exists: {dest}")

    lang = lang.lower().strip()
    if lang not in LANGS:
        raise SystemExit(
            f"unknown language {lang!r}; supported: {', '.join(LANGS)}"
        )

    tmpl = template_dir(lang)
    print(f"create {package} (lang={lang}, template={tmpl})")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(tmpl, dest, ignore=_copy_ignore)
    _clean_copied_debian(dest)

    # Never keep the template changelog; regenerate below.
    changelog = dest / "debian" / "changelog"
    if changelog.is_file():
        changelog.unlink()

    names = list(puff_names or [])
    first = names[0] if names else None
    rest = names[1:]
    print(f"instantiate zephyr → {package}" + (f", {TEMPLATE_PUFF} → {first}" if first else ""))
    pairs = instantiation_pairs(package, first)
    files, renames = rewrite_tree(dest, pairs, rename_paths=True)
    print(f"  {files} file(s) rewritten, {renames} path(s) renamed")

    if not first:
        # Drop template puff *files* only; leave content tokens so a later
        # `zfr add NAME` can rename some_puff1 → NAME in place.
        cmd_remove([TEMPLATE_PUFF], workdir=dest)
    else:
        for name in rest:
            cmd_add([name], workdir=dest)
        # Extra `add` copies from the template; rewrite again so any leftover
        # some_puff1 / zephyr tokens in skipped existing files are substituted.
        rewrite_tree(dest, instantiation_pairs(package, first), rename_paths=True)

    if first:
        leftover = _leftover_template_lines(dest)
        if leftover:
            preview = "\n".join(leftover[:40])
            more = "" if len(leftover) <= 40 else f"\n  … {len(leftover) - 40} more"
            raise SystemExit(
                f"template identifiers remain in {dest} after create "
                f"(puff1/zephyr):\n{preview}{more}"
            )
    print(
        f"debian/changelog ← {package} ({init_version}) {distribution} "
        f"({author} <{email}>)"
    )
    _write_debian_changelog(
        dest,
        package=package,
        version=init_version,
        distribution=distribution,
        author=author,
        email=email,
    )
    _install_githooks(dest)

    print(f"git init + commit + tag v{init_version.lstrip('v')}")
    print("git config core.hooksPath .githooks")
    try:
        _git_init_commit_tag(
            dest,
            version=init_version,
            author=author,
            email=email,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        raise SystemExit(f"git init/commit/tag failed: {err}") from e

    print(f"created {dest}")


NAME = "create"
HELP = _('create a new project from a language template')
DESCRIPTION = _('Create a new project directory from pkgdatadir/<lang>.')


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-l", "--lang", default="python", metavar="LANG",
        help=_("template language (default: python; one of: %s)") % ", ".join(LANGS),
    )
    p.add_argument(
        "-D", "--distribution", default=DEFAULT_DISTRIBUTION, metavar="DIST",
        help=_("debian changelog distribution (default: %s)") % DEFAULT_DISTRIBUTION,
    )
    p.add_argument(
        "-1", "--init-version", default=DEFAULT_INIT_VERSION, metavar="VER",
        help=_("initial package version and git tag (default: %s)") % DEFAULT_INIT_VERSION,
    )
    p.add_argument(
        "-a", "--author", default=DEFAULT_AUTHOR, metavar="AUTHOR",
        help=_("changelog/git author name (default: %s)") % DEFAULT_AUTHOR,
    )
    p.add_argument(
        "-e", "--email", default=DEFAULT_EMAIL, metavar="EMAIL",
        help=_("changelog/git author email (default: %s)") % DEFAULT_EMAIL,
    )
    p.add_argument("project_name", help=_("new project directory name"))
    p.add_argument(
        "puff_names", nargs="*",
        help=_("optional puff names to add after creating the project"),
    )


def run(args: argparse.Namespace) -> int:
    cmd_create(
        args.project_name,
        lang=args.lang,
        puff_names=list(args.puff_names),
        distribution=args.distribution,
        init_version=args.init_version,
        author=args.author,
        email=args.email,
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
