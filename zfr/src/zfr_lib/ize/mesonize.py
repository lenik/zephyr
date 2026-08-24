# SPDX-License-Identifier: AGPL-3.0-or-later
"""Invoke 2meson to convert Autotools/CMake trees before zephyr scaffolding."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def has_foreign_build(root: Path) -> bool:
    """True when Autotools or CMake sources are present (2meson can convert)."""
    return (
        (root / "configure.ac").is_file()
        or (root / "configure.in").is_file()
        or (root / "CMakeLists.txt").is_file()
    )


def find_2meson() -> str | None:
    """Resolve the 2meson executable (PATH, then ZFR_2MESON)."""
    env = os.environ.get("ZFR_2MESON", "").strip()
    if env:
        p = Path(env)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return shutil.which("2meson")


def run_2meson(
    root: Path,
    *,
    dry_run: bool = False,
    force: bool = True,
    verbose: bool = False,
) -> tuple[int, str]:
    """Run 2meson on *root*. Returns (exit_code, combined log text)."""
    exe = find_2meson()
    if exe is None:
        return 127, "2meson not found in PATH (set ZFR_2MESON or install 2meson)"
    cmd = [exe]
    if dry_run:
        cmd.append("-n")
    if force:
        cmd.append("-f")
    if verbose:
        cmd.append("-v")
    cmd.append(str(root))
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out
