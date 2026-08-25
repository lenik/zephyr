# SPDX-License-Identifier: AGPL-3.0-or-later
"""Layout and git-hook checks."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import (
    LANGS,
    RECOMMENDED_I18N_LINGUAS,
    RECOMMENDED_I18N_SOURCE,
    TEMPLATE_PUFF,
    _is_zfr_cli_package,
    _is_zfr_meta_repo,
    changelog_version,
    detect_lang,
    find_project_dir,
    is_probably_text,
    iter_files,
    template_dir,
    version_file_version,
)
from ..csr import Csr
from ..packaging import _meson_project_fields, _parse_control_stanzas
from .finding import Finding
from .util import *  # noqa: F403

def check_layout(root: Path, lang: str, role: str) -> list[Finding]:
    out: list[Finding] = []
    required = [
        ("meson.build", "meson.build", _("Add a top-level meson.build with project(...).")),
        ("LICENSE", "LICENSE", _("Copy LICENSE from the language template (AGPL-3.0-or-later).")),
        ("README.md", "README.md", _("Add README.md describing this project.")),
        ("README-zh.md", "README-zh.md", _("Add README-zh.md (Chinese summary), matching other zephyr templates.")),
        ("debian/control", "debian/control", _("Add debian/ packaging (copy debian/ from the language template).")),
        ("debian/changelog", "debian/changelog", _("Add debian/changelog (zfr create writes one; or use dch).")),
        ("debian/copyright", "debian/copyright", _("Add debian/copyright in machine-readable format, License: AGPL-3+.")),
        ("debian/rules", "debian/rules", _("Add debian/rules using dh --buildsystem=meson --builddirectory=debian/build.")),
        ("debian/source/format", "debian/source/format", _("Add debian/source/format (typically '3.0 (native)').")),
    ]
    for code, rel, fix in required:
        if _has_file(root, rel):
            out.append(Finding("ok", f"layout.{code.replace('/', '.')}", _("present: %s") % rel, rel))
        else:
            out.append(
                Finding("error", f"layout.{code.replace('/', '.')}", _("missing %s") % rel, rel, fix=fix)
            )

    adocs = list((root / "docs").glob("*.adoc")) if (root / "docs").is_dir() else []
    if adocs:
        out.append(
            Finding("ok", "layout.docs", _("AsciiDoc man sources: %s") % ", ".join(p.name for p in adocs), "docs/")
        )
    else:
        out.append(
            Finding(
                "error",
                "layout.docs",
                _("no docs/*.adoc man page source"),
                "docs/",
                fix=_("Add docs/<puff>.adoc and a meson custom_target with asciidoctor -b manpage "
                "(see any language template)."),
            )
        )

    completions = list(root.glob("*.bash"))
    if not completions and (root / "tools").is_dir():
        completions = list((root / "tools").glob("*.bash"))
    if completions:
        out.append(
            Finding(
                "ok",
                "layout.completion",
                _("bash completion: %s") % ", ".join(p.name for p in completions),
            )
        )
    elif role != "meta":
        out.append(
            Finding(
                "warn",
                "layout.completion",
                _("no *.bash bash-completion script at project root"),
                fix=_("Add <puff>.bash and install it to datadir/bash-completion/completions "
                "renamed to the command name (see meson.build in the template)."),
            )
        )

    if _has_file(root, "VERSION"):
        out.append(Finding("ok", "layout.VERSION", _("VERSION file present"), "VERSION"))
    else:
        out.append(
            Finding(
                "warn",
                "layout.VERSION",
                _("no VERSION file (changelog snapshot for tarball builds)"),
                "VERSION",
                fix=_("Create VERSION with the latest debian/changelog version "
                "(one line). Enable .githooks/pre-commit: git config core.hooksPath .githooks"),
            )
        )

    out.extend(_check_pre_commit(root))
    return out


def _find_git_root(start: Path) -> Path | None:
    """Nearest ancestor (inclusive) that contains a .git file or directory."""
    cur = start.resolve()
    for d in [cur, *cur.parents]:
        if (d / ".git").exists():
            return d
    return None


def _core_hooks_dir(git_root: Path) -> Path:
    """Resolve core.hooksPath relative to *git_root*, else git_root/.githooks."""
    if shutil.which("git"):
        proc = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=git_root,
            capture_output=True,
            text=True,
        )
        raw = proc.stdout.strip()
        if proc.returncode == 0 and raw:
            path = Path(raw)
            return path if path.is_absolute() else (git_root / path)
    return git_root / ".githooks"


def _pre_commit_syncs_version(hook: Path) -> bool:
    """True if *hook* updates VERSION from debian/changelog."""
    text = _read(hook)
    if not text:
        return False
    if not re.search(r"\bVERSION\b", text):
        return False
    lowered = text.lower()
    return "changelog" in lowered or "dpkg-parsechangelog" in text


def _hook_label(root: Path, hook: Path) -> str:
    try:
        return str(hook.resolve().relative_to(root.resolve()))
    except ValueError:
        pass
    git_root = _find_git_root(root)
    if git_root is not None:
        try:
            return str(hook.resolve().relative_to(git_root.resolve()))
        except ValueError:
            pass
    return str(hook)


def _check_pre_commit(root: Path) -> list[Finding]:
    """Locate .githooks from the git root, then verify VERSION-sync behavior."""
    git_root = _find_git_root(root)
    seen: set[Path] = set()
    candidates: list[Path] = []

    def _add(path: Path) -> None:
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key in seen:
            return
        seen.add(key)
        candidates.append(path)

    if git_root is not None:
        _add(_core_hooks_dir(git_root) / "pre-commit")
        _add(git_root / ".githooks" / "pre-commit")
    _add(root / ".githooks" / "pre-commit")

    chosen: Path | None = None
    for path in candidates:
        if path.is_file():
            chosen = path
            break

    if chosen is None:
        loc = ".githooks/pre-commit"
        if git_root is not None:
            loc = str((_core_hooks_dir(git_root) / "pre-commit"))
        return [
            Finding(
                "note",
                "layout.pre-commit",
                _("no .githooks/pre-commit to sync VERSION from debian/changelog"),
                loc,
                fix=_("Walk up to the directory that contains .git, then put "
                "pre-commit in that tree's .githooks (or core.hooksPath). "
                "The hook must update VERSION from debian/changelog. "
                "`zfr create` copies one and sets git config core.hooksPath .githooks."),
            )
        ]

    label = _hook_label(root, chosen)
    if _pre_commit_syncs_version(chosen):
        return [
            Finding(
                "ok",
                "layout.pre-commit",
                _("pre-commit syncs VERSION from debian/changelog (%s)") % label,
                label,
            )
        ]
    return [
        Finding(
            "warn",
            "layout.pre-commit",
            _("%s exists but does not sync VERSION from debian/changelog") % label,
            label,
            fix=_("The hook should read debian/changelog (dpkg-parsechangelog) "
            "and write VERSION. See the zephyr .githooks/pre-commit template."),
        )
    ]
