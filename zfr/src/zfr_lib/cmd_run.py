# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run a command, optionally capturing stdout/stderr into a StreamRecorder."""

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path

from .stream_mark import Which, get_recorder, log_line


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> None:
    """Run *cmd*; tee into the active StreamRecorder when one is set."""
    log_line("+ " + " ".join(cmd), which="out")
    if dry_run:
        return
    rec = get_recorder()
    if rec is None:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)
        return

    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
    )
    assert proc.stdout is not None and proc.stderr is not None

    def _pump(stream, which: Which) -> None:
        try:
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    break
                rec.write(which, chunk)
        finally:
            try:
                stream.close()
            except OSError:
                pass

    t_out = threading.Thread(target=_pump, args=(proc.stdout, "out"), daemon=True)
    t_err = threading.Thread(target=_pump, args=(proc.stderr, "err"), daemon=True)
    t_out.start()
    t_err.start()
    rc = proc.wait()
    t_out.join(timeout=30)
    t_err.join(timeout=30)
    if rc != 0:
        raise subprocess.CalledProcessError(rc, cmd)


def merge_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if extra:
        env.update(extra)
    return env
