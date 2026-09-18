# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run the native release / publish pipelines."""

from __future__ import annotations

from .build_step import step_build
from .context import Options, ctx_init
from .deb_upload import step_deb_upload
from .detect import step_detect
from .gh_release import step_gh_release
from .git_tag import step_git_tag_prepare, step_git_tag_push
from .logutil import get_log_level, log1
from .marketplace import step_marketplace_publish
from .prereqs import step_prereqs


def run_release(opts: Options) -> int:
    """Tag, build/package, install, private-cloud upload, GitHub release.

    Does **not** publish to npm / VSIX marketplaces — use ``run_publish``.
    """
    log1(f"Starting zfr release (LOGLEVEL={get_log_level()})")
    ctx = ctx_init(opts)
    step_detect(ctx)
    step_prereqs(ctx)
    step_git_tag_prepare(ctx)
    step_git_tag_push(ctx)
    step_build(ctx)
    step_deb_upload(ctx)
    step_gh_release(ctx)
    return 0


def run_publish(opts: Options) -> int:
    """Full ``run_release`` plus marketplace publish (npm / VSIX)."""
    log1(f"Starting zfr publish (LOGLEVEL={get_log_level()})")
    ctx = ctx_init(opts)
    step_detect(ctx)
    step_prereqs(ctx)
    step_git_tag_prepare(ctx)
    step_git_tag_push(ctx)
    step_build(ctx)
    step_deb_upload(ctx)
    step_gh_release(ctx)
    step_marketplace_publish(ctx)
    return 0
