# SPDX-License-Identifier: AGPL-3.0-or-later
"""GitHub release notes and gh release create."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from .logutil import log1, run

from .artifacts import step_collect_artifacts
from .context import Context


def get_release_notes(
    project_type: str,
    projectdir: Path | str,
    version: str,
) -> str:
    """Write release notes to a temp file; return its path."""
    projectdir = Path(projectdir)
    fd, notes_path = tempfile.mkstemp(prefix="zfr-release-notes-", text=True)
    with open(fd, "w", encoding="utf-8") as notes:
        if project_type == "debian":
            changelog = projectdir / "debian" / "changelog"
            notes.write(f"Release {version}\n\n")
            parsed = subprocess.run(
                [
                    "dpkg-parsechangelog",
                    "-l",
                    str(changelog),
                    "-S",
                    "Changes",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            bullets: list[str] = []
            if parsed.returncode == 0 and parsed.stdout:
                for line in parsed.stdout.splitlines():
                    if line.startswith("  * "):
                        bullets.append("- " + line[4:])
            else:
                with changelog.open(encoding="utf-8") as fh:
                    for line in fh:
                        if line.startswith("  * "):
                            bullets.append("- " + line[4:].rstrip("\n"))
                        elif re.match(r"^  -- ", line):
                            break
            for b in bullets:
                notes.write(b + "\n")
            notes.write("\nSee README.md and debian/changelog.\n")
        elif project_type in ("vsix", "nodejs"):
            log1("Getting release notes from recent commit")
            notes.write(f"Release {version}\n\n")
            body = subprocess.check_output(
                ["git", "log", "-1", "--format=%B"],
                text=True,
            )
            notes.write(body)
            if not body.endswith("\n"):
                notes.write("\n")
            notes.write("\n")

    return notes_path


def step_gh_release(ctx: Context) -> None:
    if ctx.opts.local or ctx.opts.no_release:
        if ctx.opts.no_release and not ctx.opts.local:
            log1("Skipping GitHub release (--no-release)")
        return

    step_collect_artifacts(ctx)

    ctx.notes = get_release_notes(
        ctx.project_type, ctx.projectdir, ctx.version
    )
    try:
        log1(f"Creating GitHub release {ctx.tag}")
        run(
            "gh",
            "release",
            "create",
            ctx.tag,
            ctx.tarball,
            *ctx.attachments,
            "--title",
            ctx.tag,
            "--notes-file",
            ctx.notes,
        )
        print(f"Created release {ctx.tag}")
    finally:
        try:
            Path(ctx.notes).unlink(missing_ok=True)
        except OSError:
            pass
