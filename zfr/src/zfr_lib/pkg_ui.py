# SPDX-License-Identifier: AGPL-3.0-or-later
"""Live packaging status lines and interactive lasterror browser."""

from __future__ import annotations

import curses
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from .csr import Csr, term_columns
from .pkg_last import PackagerRecord, PackageLastRun
from .stream_mark import decode_marked, replay_marked


@dataclass
class PackagerState:
    name: str
    status: str = "pending"  # pending | running | ok | fail
    tip: str = ""
    summary: str = ""
    error: str = ""
    marked: str = ""


@dataclass
class StatusBoard:
    """Multi-line live status for parallel packagers (TTY only)."""

    title: str = "Packaging..."
    states: list[PackagerState] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _printed: int = 0
    _csr: Csr = field(default_factory=Csr)
    enabled: bool = field(default_factory=lambda: sys.stdout.isatty())

    def set_tip(self, name: str, tip: str) -> None:
        with self._lock:
            for s in self.states:
                if s.name == name:
                    if s.status == "running":
                        s.tip = tip
                    break
            self._redraw_unlocked()

    def set_running(self, name: str) -> None:
        with self._lock:
            for s in self.states:
                if s.name == name:
                    s.status = "running"
                    s.tip = "…"
                    break
            self._redraw_unlocked()

    def set_ok(self, name: str, summary: str = "packaged") -> None:
        with self._lock:
            for s in self.states:
                if s.name == name:
                    s.status = "ok"
                    s.summary = summary
                    s.tip = summary
                    break
            self._redraw_unlocked()

    def set_fail(self, name: str, error: str) -> None:
        with self._lock:
            for s in self.states:
                if s.name == name:
                    s.status = "fail"
                    s.error = error
                    s.summary = f"error: {error}"
                    s.tip = s.summary
                    break
            self._redraw_unlocked()

    def start(self) -> None:
        with self._lock:
            self._redraw_unlocked()

    def finish(self) -> None:
        """Leave the final status block on screen (no cursor rewind)."""
        with self._lock:
            self._printed = 0

    def _line_for(self, s: PackagerState) -> str:
        label = f"[ {s.name} ]"
        width = term_columns()
        if s.status == "ok":
            mark = self._csr.sev("ok", "✓")
            body = s.summary or "packaged"
            text = f"    {label} {mark} {body}"
        elif s.status == "fail":
            mark = self._csr.sev("error", "✗")
            body = s.summary or "error"
            text = f"    {label} {mark} {body}"
        elif s.status == "running":
            tip = s.tip or "…"
            text = f"    {label} {tip}"
        else:
            text = f"    {label} …"
        if len(text) > width - 1:
            text = text[: width - 4] + "..."
        return text

    def _redraw_unlocked(self) -> None:
        if not self.enabled:
            return
        lines = [self.title] + [self._line_for(s) for s in self.states]
        # Rewind previous block
        if self._printed > 0:
            sys.stdout.write(f"\033[{self._printed}A")
            for _ in range(self._printed):
                sys.stdout.write("\033[2K\033[1B")
            sys.stdout.write(f"\033[{self._printed}A")
        for ln in lines:
            sys.stdout.write("\033[2K" + ln + "\n")
        sys.stdout.flush()
        self._printed = len(lines)


def format_record_line(rec: PackagerRecord, *, csr: Csr | None = None) -> str:
    csr = csr or Csr()
    label = f"[ {rec.name} ]"
    if rec.ok:
        return f"    {label} {csr.sev('ok', '✓')} {rec.summary or 'packaged'}"
    return f"    {label} {csr.sev('error', '✗')} {rec.summary or rec.error or 'error'}"


def print_run_summary(run: PackageLastRun) -> None:
    csr = Csr()
    print("Packaging...", flush=True)
    for rec in run.records:
        print(format_record_line(rec, csr=csr), flush=True)


def _detail_text(rec: PackagerRecord) -> str:
    parts: list[str] = []
    for which, data in decode_marked(rec.marked):
        tag = "OUT" if which == "out" else "ERR"
        parts.append(f"── {tag} ──\n{data}")
    if not parts:
        return "(no captured output)\n"
    return "\n".join(parts)


def interactive_lasterror(
    run: PackageLastRun,
    *,
    only_failures: bool = False,
    on_enter: Callable[[PackagerRecord], None] | None = None,
) -> int:
    """Curses UI: list packagers, Tab=detail, Enter=replay, q=quit.

    Returns 0 on success/quit, 1 if no records.
    """
    records = run.failures() if only_failures else list(run.records)
    if not records:
        print("zfr lasterror: no package records", file=sys.stderr)
        return 1
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print_run_summary(run)
        print(
            "zfr lasterror: not a TTY; use Enter path unavailable. "
            "Showing summary only.",
            file=sys.stderr,
        )
        return 0

    def _default_enter(rec: PackagerRecord) -> None:
        replay_marked(rec.marked)

    enter_cb = on_enter or _default_enter
    result_hold: list[PackagerRecord | None] = [None]

    def _curses_main(stdscr: curses.window) -> None:
        curses.curs_set(0)
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(2, curses.COLOR_RED, -1)
            curses.init_pair(3, curses.COLOR_CYAN, -1)
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)

        idx = 0
        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            title = "zfr lasterror — ↑/↓ select  Tab detail  Enter replay  q quit"
            stdscr.addnstr(0, 0, title, max(0, w - 1), curses.A_BOLD)
            for i, rec in enumerate(records):
                y = i + 2
                if y >= h - 1:
                    break
                mark = "✓" if rec.ok else "✗"
                line = f"  [ {rec.name} ] {mark} {rec.summary or rec.error or ''}"
                attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
                if curses.has_colors() and i != idx:
                    attr |= curses.color_pair(1 if rec.ok else 2)
                stdscr.addnstr(y, 0, line.ljust(max(0, w - 1))[: w - 1], w - 1, attr)
            stdscr.refresh()

            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q"), 27):  # q or Esc at list → quit
                return
            if ch in (curses.KEY_UP, ord("k")):
                idx = (idx - 1) % len(records)
            elif ch in (curses.KEY_DOWN, ord("j")):
                idx = (idx + 1) % len(records)
            elif ch in (9,):  # Tab → detail
                _show_detail(stdscr, records[idx])
            elif ch in (curses.KEY_ENTER, 10, 13):
                result_hold[0] = records[idx]
                return

    def _show_detail(stdscr: curses.window, rec: PackagerRecord) -> None:
        text = _detail_text(rec)
        lines = text.splitlines() or [""]
        top = 0
        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            hdr = f"[ {rec.name} ] detail — Esc/q back  ↑/↓ scroll"
            stdscr.addnstr(0, 0, hdr, max(0, w - 1), curses.A_BOLD)
            view = h - 2
            for i in range(view):
                li = top + i
                if li >= len(lines):
                    break
                stdscr.addnstr(i + 1, 0, lines[li][: w - 1], w - 1)
            stdscr.refresh()
            ch = stdscr.getch()
            if ch in (27, ord("q"), ord("Q")):
                return
            if ch in (curses.KEY_UP, ord("k")):
                top = max(0, top - 1)
            elif ch in (curses.KEY_DOWN, ord("j")):
                top = min(max(0, len(lines) - view), top + 1)
            elif ch == curses.KEY_PPAGE:
                top = max(0, top - view)
            elif ch == curses.KEY_NPAGE:
                top = min(max(0, len(lines) - view), top + view)

    curses.wrapper(_curses_main)
    chosen = result_hold[0]
    if chosen is not None:
        # Leave curses before writing to real stdout/stderr
        enter_cb(chosen)
    return 0
