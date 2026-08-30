# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize engine helpers — optional git commit after ize."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from ... import changelog_version, version_file_version
from ...create import DEFAULT_INIT_VERSION
from ..util import bump_patch_version, prepend_debian_changelog

if TYPE_CHECKING:
    from . import Ize


def commit_message(ize: "Ize") -> str:
    """Build a verbose commit message from recorded ize changes."""
    real = [c for c in ize.changes if c.kind in {"add", "update", "convert"}]
    adds = sum(1 for c in real if c.kind == "add")
    updates = sum(1 for c in real if c.kind == "update")
    converts = sum(1 for c in real if c.kind == "convert")
    ver = getattr(ize, "_commit_version", None)
    if ver:
        subject = (
            f"zfr ize: {ize.name} {ver} (lang={ize.lang}) — "
            "align to current zephyr style"
        )
    else:
        subject = (
            f"zfr ize: align {ize.name} (lang={ize.lang}) to current zephyr style"
        )
    lines = [
        subject,
        "",
        f"Automated `zfr ize` on {ize.name}: bring packaging, Meson, man pages,",
        "and version substitutions up to current zephyr style.",
        "",
    ]
    if ver:
        lines.append(f"Version: {ver} (debian/changelog + VERSION).")
        lines.append("")
    if real:
        lines.append("Changes:")
        for c in real:
            lines.append(f"  - {c.kind:7} {c.path}: {c.detail}")
        lines.append("")
    lines.append(
        f"{adds} added, {updates} updated, {converts} converted"
        + ("; mesonized via 2meson" if ize._mesonized else "")
        + "."
    )
    lines.append("")
    return "\n".join(lines)

def changelog_bullets(ize: "Ize") -> list[str]:
    """Short debian/changelog bullets from recorded ize changes."""
    real = [c for c in ize.changes if c.kind in {"add", "update", "convert"}]
    bullets: list[str] = [
        "Align packaging/Meson/man pages to current zephyr style (zfr ize)."
    ]
    if ize._mesonized:
        bullets.append("Convert Autotools/CMake to Meson via 2meson.")
    # Cap path-level detail so the stanza stays readable.
    for c in real[:12]:
        bullets.append(f"{c.kind} {c.path}: {c.detail}")
    if len(real) > 12:
        bullets.append(f"…and {len(real) - 12} more path updates.")
    return bullets

def bump_for_commit(ize: "Ize") -> str | None:
    """Bump patch version, prepend debian/changelog, sync VERSION.

    Called by ``--commit`` when ize actually changed the tree. Returns
    the new version, or None when there is nothing to bump.
    """
    real = [c for c in ize.changes if c.kind in {"add", "update", "convert"}]
    if not real and not ize._mesonized:
        return None
    if ize.dry_run:
        return None
    old = (
        changelog_version(ize.root)
        or version_file_version(ize.root)
        or DEFAULT_INIT_VERSION
    )
    new = bump_patch_version(old)
    prepend_debian_changelog(
        ize.root,
        package=ize.name,
        version=new,
        bullets=changelog_bullets(ize),
        author_override=ize.author,
    )
    ize.note("update", "debian/changelog", f"{old} → {new}")
    ize.note("update", "VERSION", new)
    ize._commit_version = new
    print(f"zfr ize --commit: version {old} → {new}", flush=True)
    return new

def commit_changes(ize: "Ize") -> None:
    """Bump changelog/VERSION, then ``git add -A`` and commit."""
    import subprocess

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=ize.root,
            check=check,
            capture_output=True,
            text=True,
        )

    try:
        git("rev-parse", "--is-inside-work-tree")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise SystemExit(
            f"zfr ize --commit: {ize.root} is not a git working tree"
        ) from e

    real = [c for c in ize.changes if c.kind in {"add", "update", "convert"}]
    if not real and not ize._mesonized:
        print("zfr ize --commit: no ize changes to commit.", flush=True)
        return

    bump_for_commit(ize)

    git("add", "-A")
    staged = git("diff", "--cached", "--quiet", check=False)
    if staged.returncode == 0:
        print(
            "zfr ize --commit: working tree clean after ize; nothing to commit.",
            flush=True,
        )
        return

    msg = commit_message(ize)
    try:
        git("commit", "-m", msg)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip() or str(e)
        raise SystemExit(f"zfr ize --commit failed: {err}") from e
    sha = git("rev-parse", "--short", "HEAD").stdout.strip()
    print(f"committed {sha}: {msg.splitlines()[0]}", flush=True)
