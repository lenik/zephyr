# SPDX-License-Identifier: AGPL-3.0-or-later
"""Marketplace / registry publish (npm and VSIX).

Called by ``zfr publish`` after a successful release pipeline. Not part of
``zfr release`` (which stops at private-cloud package upload).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .context import Context
from .logutil import log1, quit
from .util import read_identity_token


def publish_vsix_marketplaces(
    projectdir: Path | str,
    pkgname: str,
    version: str,
) -> None:
    projectdir = Path(projectdir)
    vsix_rel = f"{pkgname}-{version}.vsix"
    vsix = projectdir / vsix_rel
    vs_id = Path.home() / ".identity" / "azure-devops.id"
    ovsx_id = Path.home() / ".identity" / "open-vsx.id"

    if not vsix.is_file():
        quit(f"VSIX not found: {vsix}")

    vs_pat = read_identity_token(vs_id)
    ovsx_pat = read_identity_token(ovsx_id)

    if not vs_pat:
        log1(f"  Skip Visual Studio Marketplace (no token in {vs_id})")
    else:
        log1("Publishing to Visual Studio Marketplace...")
        env = {**os.environ, "VSCE_PAT": vs_pat}
        r = subprocess.run(
            ["pnpm", "exec", "vsce", "publish", "--packagePath", vsix_rel],
            cwd=str(projectdir),
            env=env,
            check=False,
        )
        if r.returncode != 0:
            quit("vsce publish failed.")

    if not ovsx_pat:
        log1(f"  Skip Open VSX (no token in {ovsx_id})")
    else:
        log1("Publishing to Open VSX...")
        env = {**os.environ, "OVSX_PAT": ovsx_pat}
        r = subprocess.run(
            ["pnpm", "exec", "ovsx", "publish", vsix_rel],
            cwd=str(projectdir),
            env=env,
            check=False,
        )
        if r.returncode != 0:
            quit("ovsx publish failed.")


def publish_npm_registry(projectdir: Path | str) -> None:
    """Publish a nodejs package with pnpm or npm."""
    projectdir = Path(projectdir)
    runner = shutil.which("pnpm") or shutil.which("npm")
    if not runner:
        quit("pnpm/npm not found (required for npm registry publish).")
    log1(f"Publishing to npm registry via {Path(runner).name}...")
    r = subprocess.run([runner, "publish"], cwd=str(projectdir), check=False)
    if r.returncode != 0:
        quit("npm publish failed.")


def step_marketplace_publish(ctx: Context) -> None:
    """Publish to public marketplaces when defined for this project type."""
    if ctx.opts.local:
        log1("Skipping marketplace publish (local)")
        return

    if ctx.project_type == "vsix":
        publish_vsix_marketplaces(ctx.projectdir, ctx.pkgname, ctx.version)
        return
    if ctx.project_type == "nodejs":
        publish_npm_registry(ctx.projectdir)
        return

    log1(
        f"No marketplace publish defined for project type "
        f"{ctx.project_type!r} (currently: npm, vsix)"
    )
