# SPDX-License-Identifier: AGPL-3.0-or-later
"""Marked stdout/stderr capture for parallel packaging.

Chunks are stored as ``<out>…</out><err>…</err>`` so they can be replayed
to the real stdout/stderr in original order. Payload text escapes
literal close tags as ``&lt;/out&gt;`` / ``&lt;/err&gt;``.
"""

from __future__ import annotations

import contextvars
import re
import sys
import threading
from dataclasses import dataclass, field
from typing import Literal, TextIO

Which = Literal["out", "err"]

_OUT_OPEN = "<out>"
_OUT_CLOSE = "</out>"
_ERR_OPEN = "<err>"
_ERR_CLOSE = "</err>"

_ESCAPE = {
    _OUT_CLOSE: "&lt;/out&gt;",
    _ERR_CLOSE: "&lt;/err&gt;",
}
_UNESCAPE = {v: k for k, v in _ESCAPE.items()}

_CHUNK_RE = re.compile(
    r"<(out|err)>(.*?)</\1>",
    re.DOTALL,
)


def escape_payload(text: str) -> str:
    for raw, esc in _ESCAPE.items():
        text = text.replace(raw, esc)
    return text


def unescape_payload(text: str) -> str:
    for esc, raw in _UNESCAPE.items():
        text = text.replace(esc, raw)
    return text


def encode_marked(chunks: list[tuple[Which, str]]) -> str:
    parts: list[str] = []
    for which, data in chunks:
        if not data:
            continue
        payload = escape_payload(data)
        if which == "out":
            parts.append(f"{_OUT_OPEN}{payload}{_OUT_CLOSE}")
        else:
            parts.append(f"{_ERR_OPEN}{payload}{_ERR_CLOSE}")
    return "".join(parts)


def decode_marked(marked: str) -> list[tuple[Which, str]]:
    out: list[tuple[Which, str]] = []
    for m in _CHUNK_RE.finditer(marked):
        which = m.group(1)  # type: ignore[assignment]
        assert which in ("out", "err")
        out.append((which, unescape_payload(m.group(2))))  # type: ignore[arg-type]
    return out


def replay_marked(marked: str, *, out: TextIO | None = None, err: TextIO | None = None) -> None:
    """Write marked chunks back to *out*/*err* preserving order."""
    out_f = out if out is not None else sys.stdout
    err_f = err if err is not None else sys.stderr
    for which, data in decode_marked(marked):
        if which == "out":
            out_f.write(data)
            out_f.flush()
        else:
            err_f.write(data)
            err_f.flush()


@dataclass
class StreamRecorder:
    """Thread-safe marked stream accumulator with a live 'last line' tip."""

    chunks: list[tuple[Which, str]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _last_line: str = ""
    _line_buf: dict[Which, str] = field(default_factory=lambda: {"out": "", "err": ""})

    def write(self, which: Which, data: str) -> None:
        if not data:
            return
        with self._lock:
            self.chunks.append((which, data))
            buf = self._line_buf[which] + data
            parts = buf.split("\n")
            self._line_buf[which] = parts[-1]
            for line in parts[:-1]:
                tip = line.strip()
                if tip:
                    self._last_line = tip
            if self._line_buf[which].strip():
                # show partial line while running
                self._last_line = self._line_buf[which].strip()

    def marked(self) -> str:
        with self._lock:
            return encode_marked(list(self.chunks))

    def last_line(self) -> str:
        with self._lock:
            return self._last_line

    def replay(self, *, out: TextIO | None = None, err: TextIO | None = None) -> None:
        replay_marked(self.marked(), out=out, err=err)


_current_recorder: contextvars.ContextVar[StreamRecorder | None] = contextvars.ContextVar(
    "zfr_stream_recorder",
    default=None,
)


def get_recorder() -> StreamRecorder | None:
    return _current_recorder.get()


def set_recorder(rec: StreamRecorder | None) -> contextvars.Token:
    return _current_recorder.set(rec)


def reset_recorder(token: contextvars.Token) -> None:
    _current_recorder.reset(token)


def log_line(msg: str, *, which: Which = "out") -> None:
    """Print *msg* (plus newline) to the active recorder or real streams."""
    text = msg if msg.endswith("\n") else msg + "\n"
    rec = get_recorder()
    if rec is not None:
        rec.write(which, text)
        return
    if which == "out":
        sys.stdout.write(text)
        sys.stdout.flush()
    else:
        sys.stderr.write(text)
        sys.stderr.flush()
