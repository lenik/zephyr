# SPDX-License-Identifier: AGPL-3.0-or-later
"""Less-style help overlay for ``zfr lasterror`` (logs open in fdmpager)."""

from __future__ import annotations

import curses

LIST_HELP_LINES = (
    "zfr lasterror",
    "",
    "  Up/Down, j/k   Select packager",
    "  Tab            Open captured log in fdmpager",
    "  Enter          Replay with fddemux",
    "  F1, ?          This help",
    "  q, Esc         Quit",
    "",
    "  Press any key to close this help.",
)


def init_log_colors() -> None:
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)


def _add(win: curses.window, y: int, x: int, text: str, attr: int = 0) -> int:
    """Write *text* at (*y*, *x*); return the next column. Never raises."""
    try:
        h, w = win.getmaxyx()
    except curses.error:
        return x
    if y < 0 or x < 0 or y >= h or x >= w or not text:
        return x
    n = max(0, w - x - 1)
    if n <= 0:
        return x
    try:
        win.addnstr(y, x, text, n, attr)
    except curses.error:
        return x
    return x + min(len(text), n)


def draw_help_overlay(stdscr: curses.window, lines: tuple[str, ...] | list[str]) -> None:
    h, _w = stdscr.getmaxyx()
    for i, line in enumerate(lines):
        y = 1 + i
        if y >= h - 1:
            break
        attr = curses.A_BOLD if i == 0 else curses.A_NORMAL
        _add(stdscr, y, 0, line, attr)


def wait_help(stdscr: curses.window, lines: tuple[str, ...] | list[str]) -> None:
    while True:
        stdscr.erase()
        _add(stdscr, 0, 0, "Help  (any key closes)", curses.A_BOLD)
        draw_help_overlay(stdscr, lines)
        stdscr.refresh()
        ch = stdscr.getch()
        if ch != curses.KEY_RESIZE:
            return
