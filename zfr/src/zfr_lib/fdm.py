# SPDX-License-Identifier: AGPL-3.0-or-later
"""FDM text helpers, per-packager capture, and fddemux/fdmpager invocation."""

from __future__ import annotations

import contextvars
import os
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Which = Literal["out", "err"]

CHAN_OUT = 1
CHAN_ERR = 2
_CHAN = {"out": CHAN_OUT, "err": CHAN_ERR}

FDMUX_MISSING = "zfr: fdmux not found (install the fdmux package)"


def which_fdm_tool(name: str) -> str | None:
    return shutil.which(name)


def require_fdm_tool(name: str) -> str:
    tool = which_fdm_tool(name)
    if not tool:
        raise SystemExit(FDMUX_MISSING)
    return tool


def _seconds_text(ts: float) -> str:
    if ts < 0:
        ts = 0.0
    whole = int(ts)
    usec = int(round((ts - whole) * 1_000_000.0))
    if usec >= 1_000_000:
        whole += 1
        usec = 0
    return f"{whole}.{usec:06d}"


def encode_run(channel: int, payload: bytes | str, *, ts: float | None = None) -> bytes:
    """Encode one text FDM run (``\\fd;`` / ``\\fd,seconds;``)."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    if not payload:
        return b""
    esc = payload.replace(b"\\", b"\\\\")
    if ts is not None:
        head = f"\\{channel},{_seconds_text(ts)};".encode("ascii")
    else:
        head = f"\\{channel};".encode("ascii")
    return head + esc


def iter_runs(data: bytes) -> list[tuple[int, bytes]]:
    """Parse text FDM runs. Truncated / invalid tails are dropped."""
    if not data:
        return []
    if data[0:1] != b"\\":
        return []
    out: list[tuple[int, bytes]] = []
    i = 1
    n = len(data)
    while i < n:
        if not (48 <= data[i] <= 57):  # digit
            break
        fd = 0
        while i < n and 48 <= data[i] <= 57:
            fd = fd * 10 + (data[i] - 48)
            i += 1
            if fd > 255:
                return out
        if fd == 0:
            break
        if i < n and data[i] == 44:  # comma — skip timestamp
            i += 1
            while i < n and data[i] != 59:  # semicolon
                i += 1
        if i >= n or data[i] != 59:
            break
        i += 1
        payload = bytearray()
        while i < n:
            c = data[i]
            if c != 92:  # backslash
                payload.append(c)
                i += 1
                continue
            if i + 1 >= n:
                break
            nxt = data[i + 1]
            if nxt == 92:
                payload.append(92)
                i += 2
                continue
            if 48 <= nxt <= 57:
                i += 1  # next loop starts at the digit
                break
            return out
        out.append((fd, bytes(payload)))
    return out


def last_line_from_fdm(data: bytes) -> str:
    """Last non-empty stripped line across all run payloads (live status tip)."""
    last = ""
    for _ch, payload in iter_runs(data):
        text = payload.decode("utf-8", errors="replace")
        parts = text.split("\n")
        for line in parts[:-1]:
            tip = line.strip()
            if tip:
                last = tip
        if parts[-1].strip():
            last = parts[-1].strip()
    return last


@dataclass
class FdmCapture:
    """Thread-safe append-only text FDM file for one packager."""

    path: Path
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def append_run(self, channel: int, payload: bytes | str) -> None:
        blob = encode_run(channel, payload)
        if not blob:
            return
        with self._lock:
            with self.path.open("ab") as f:
                f.write(blob)

    def append_fdm(self, src: Path) -> None:
        data = src.read_bytes()
        if not data:
            return
        with self._lock:
            with self.path.open("ab") as f:
                f.write(data)

    def last_line(self) -> str:
        try:
            with self._lock:
                data = self.path.read_bytes()
        except OSError:
            return ""
        return last_line_from_fdm(data)


_current: contextvars.ContextVar[FdmCapture | None] = contextvars.ContextVar(
    "zfr_fdm_capture",
    default=None,
)


def get_capture() -> FdmCapture | None:
    return _current.get()


def set_capture(cap: FdmCapture | None) -> contextvars.Token:
    return _current.set(cap)


def reset_capture(token: contextvars.Token) -> None:
    _current.reset(token)


def log_line(msg: str, *, which: Which = "out") -> None:
    """Print *msg* (plus newline) to the active FDM capture or real streams."""
    import sys

    text = msg if msg.endswith("\n") else msg + "\n"
    cap = get_capture()
    if cap is not None:
        cap.append_run(_CHAN[which], text)
        return
    stream = sys.stdout if which == "out" else sys.stderr
    stream.write(text)
    stream.flush()


def fdmux_capture(cmd: list[str], dest: FdmCapture, *, cwd: Path | None = None, env: dict[str, str] | None = None) -> int:
    """Run *cmd* under ``fdmux -n`` and append the capture onto *dest*."""
    fdmux = require_fdm_tool("fdmux")
    fd, tmp = tempfile.mkstemp(prefix="zfr-fdm-", suffix=".fdm")
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        proc = subprocess.run(
            [fdmux, "-n", "-o", str(tmp_path), "--", *cmd],
            cwd=cwd,
            env=env,
        )
        dest.append_fdm(tmp_path)
        return proc.returncode
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


def demux_file(path: str | Path) -> int:
    tool = require_fdm_tool("fddemux")
    return subprocess.call([tool, str(path)])


def page_files(paths: list[str | Path]) -> int:
    tool = require_fdm_tool("fdmpager")
    if not paths:
        return 0
    return subprocess.call([tool, *[str(p) for p in paths]])
