# SPDX-License-Identifier: AGPL-3.0-or-later
"""Git tag create / push / force-replace for the release tag."""

from __future__ import annotations

import subprocess

from .logutil import log1, quit, run

from .context import Context


def tag_points_at_head(tag: str) -> bool:
    tip = subprocess.run(
        ["git", "rev-parse", f"{tag}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if tip.returncode != 0:
        return False
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    return tip.stdout.strip() == head


def remote_tag_points_at_head(tag: str) -> bool:
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    remote_sha = ""
    peeled = subprocess.run(
        ["git", "ls-remote", "origin", f"refs/tags/{tag}^{{}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if peeled.stdout.strip():
        remote_sha = peeled.stdout.split()[0]
    if not remote_sha:
        plain = subprocess.run(
            ["git", "ls-remote", "origin", f"refs/tags/{tag}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if plain.stdout.strip():
            remote_sha = plain.stdout.split()[0]
    return bool(remote_sha) and remote_sha == head_sha


def _local_tag_exists(tag: str) -> bool:
    r = subprocess.run(
        ["git", "rev-parse", tag],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return r.returncode == 0


def _remote_tag_exists(tag: str) -> bool:
    r = subprocess.run(
        ["git", "ls-remote", "origin", f"refs/tags/{tag}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(r.stdout.strip())


def step_git_tag_prepare(ctx: Context) -> None:
    """Ensure tag/release can be created (or force-replaced). No-op when --local/--no-tag."""
    opts = ctx.opts
    if opts.local or opts.no_tag:
        return

    if not opts.force:
        if _local_tag_exists(ctx.tag):
            if tag_points_at_head(ctx.tag):
                log1(f"Tag {ctx.tag} already points at HEAD; reusing")
            else:
                quit(
                    f"Tag {ctx.tag} already exists locally (not on HEAD). "
                    "Use -f to replace."
                )
        if _remote_tag_exists(ctx.tag):
            if remote_tag_points_at_head(ctx.tag):
                log1(f"Origin tag {ctx.tag} already points at HEAD; reusing")
            else:
                quit(
                    f"Tag {ctx.tag} already exists on origin (not on HEAD). "
                    "Use -f to replace."
                )
        if not opts.no_release:
            view = subprocess.run(
                ["gh", "release", "view", ctx.tag],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if view.returncode == 0:
                quit(f"Release {ctx.tag} already exists. Use -f to replace.")
    else:
        log1("Force: deleting existing release and tag if present")
        if not opts.no_release:
            subprocess.run(
                ["gh", "release", "delete", ctx.tag, "--cleanup-tag", "-y"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        subprocess.run(
            ["git", "tag", "-d", ctx.tag],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def step_git_tag_push(ctx: Context) -> None:
    """Create local tag and push to origin. No-op when --local/--no-tag."""
    opts = ctx.opts
    if opts.local or opts.no_tag:
        return

    if not _local_tag_exists(ctx.tag):
        log1(f"Creating tag {ctx.tag}")
        run("git", "tag", ctx.tag)

    if opts.force:
        run("git", "push", "-f", "origin", ctx.tag)
    else:
        if remote_tag_points_at_head(ctx.tag):
            log1(f"Skipping push: origin/{ctx.tag} already at HEAD")
        else:
            run("git", "push", "origin", ctx.tag)
