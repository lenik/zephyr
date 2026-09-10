# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run a command, optionally capturing stdout/stderr via fdmux into an FDM file."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .fdm import fdmux_capture, get_capture, log_line


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> None:
    """Run *cmd*; capture through fdmux when an FDM capture is active."""
    log_line("+ " + " ".join(cmd), which="out")
    if dry_run:
        return
    cap = get_capture()
    if cap is None:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)
        return
    rc = fdmux_capture(cmd, cap, cwd=cwd, env=env)
    if rc != 0:
        raise subprocess.CalledProcessError(rc, cmd)


def merge_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if extra:
        env.update(extra)
    return env
