# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared paths and helpers for zfr test suites."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
TOOLS = ROOT / "src"
ZEPHYR = TOOLS / "zfr"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    extra = str(TOOLS)
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = extra if not prev else extra + os.pathsep + prev
    env["ZFR_PKGDATADIR"] = str(REPO)
    env["NO_COLOR"] = "1"
    env["GIT_AUTHOR_NAME"] = "Zephyr Tests"
    env["GIT_AUTHOR_EMAIL"] = "zephyr-tests@example.com"
    env["GIT_COMMITTER_NAME"] = "Zephyr Tests"
    env["GIT_COMMITTER_EMAIL"] = "zephyr-tests@example.com"
    return env


def run_zephyr(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(ZEPHYR), *args],
        cwd=cwd or ROOT,
        env=_env(),
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"zfr {' '.join(args)} failed ({proc.returncode})\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def add_src_to_path() -> None:
    sys.path.insert(0, str(TOOLS))
