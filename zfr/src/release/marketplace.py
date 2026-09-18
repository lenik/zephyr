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


def _pnpm_global_bin(name: str) -> Path | None:
    """Resolve *name* under ``pnpm bin -g`` when present."""
    if shutil.which("pnpm") is None:
        return None
    proc = subprocess.run(
        ["pnpm", "bin", "-g"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    bin_dir = proc.stdout.strip()
    if not bin_dir:
        return None
    candidate = Path(bin_dir) / name
    return candidate if candidate.is_file() else None


def _pnpm_exec_has(name: str, *, cwd: Path) -> bool:
    """True when ``pnpm exec *name*`` resolves in *cwd* (local dependency)."""
    if shutil.which("pnpm") is None:
        return False
    proc = subprocess.run(
        ["pnpm", "exec", name, "--version"],
        cwd=str(cwd),
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def ensure_pnpm_cli(name: str, npm_package: str, *, cwd: Path) -> list[str]:
    """Return argv to run a VSIX CLI (*name*), installing it globally if needed.

    Prefers PATH, then ``pnpm exec`` (project-local), then ``pnpm add -g`` and
    PATH / ``pnpm bin -g``.
    """
    which = shutil.which(name)
    if which:
        return [which]
    if _pnpm_exec_has(name, cwd=cwd):
        return ["pnpm", "exec", name]

    if shutil.which("pnpm") is None:
        quit(f"pnpm not found (required to install {npm_package} / run {name}).")

    log1(f"  {name} not found; installing with: pnpm add -g {npm_package}")
    inst = subprocess.run(
        ["pnpm", "add", "-g", npm_package],
        check=False,
    )
    if inst.returncode != 0:
        quit(f"pnpm add -g {npm_package} failed.")

    which = shutil.which(name)
    if which:
        return [which]
    global_bin = _pnpm_global_bin(name)
    if global_bin is not None:
        return [str(global_bin)]

    quit(
        f"{name} still not on PATH after pnpm add -g {npm_package}. "
        f"Ensure pnpm's global bin dir is on PATH (pnpm bin -g)."
    )


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
        # Binary is ``vsce``; npm package is ``@vscode/vsce`` (also provides ``vsce``).
        vsce = ensure_pnpm_cli("vsce", "@vscode/vsce", cwd=projectdir)
        r = subprocess.run(
            [*vsce, "publish", "--packagePath", vsix_rel],
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
        ovsx = ensure_pnpm_cli("ovsx", "ovsx", cwd=projectdir)
        r = subprocess.run(
            [*ovsx, "publish", vsix_rel],
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
