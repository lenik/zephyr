# SPDX-License-Identifier: AGPL-3.0-or-later
"""Console SGR (CSR) highlighting and column-aware text wrapping."""

from __future__ import annotations

import os
import re
import shutil
import sys
import textwrap


class Csr:
    """Console SGR renderer. Enabled when stdout is a TTY unless NO_COLOR is set."""

    reset = "\033[0m"
    bold = "\033[1m"
    dim = "\033[2m"
    red = "\033[31m"
    green = "\033[32m"
    yellow = "\033[33m"
    blue = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"

    def __init__(self, mode: str = "auto") -> None:
        if mode == "always":
            self.on = True
        elif mode == "never":
            self.on = False
        else:
            no_color = os.environ.get("NO_COLOR", "")
            self.on = sys.stdout.isatty() and not no_color

    def wrap(self, text: str, *parts: str) -> str:
        if not self.on or not parts:
            return text
        return "".join(parts) + text + self.reset

    def sev(self, severity: str, text: str) -> str:
        color = {
            "error": self.red,
            "warn": self.yellow,
            "note": self.cyan,
            "ok": self.green,
        }.get(severity, "")
        return self.wrap(text, self.bold, color)


def term_columns(fallback: int = 80) -> int:
    env = os.environ.get("COLUMNS", "").strip()
    if env.isdigit():
        cols = int(env)
    else:
        try:
            cols = shutil.get_terminal_size(fallback=(fallback, 24)).columns
        except OSError:
            cols = fallback
    return max(40, cols)


def wrap_text(text: str, width: int) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text.replace("\r", "")).strip()
    if not text:
        return []
    if width < 8:
        width = 8
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [text]


def split_commas(text: str) -> list[str]:
    """Split a dependency-style list on commas that are not inside parentheses."""
    flat = re.sub(r"[ \t]*\n[ \t]*", " ", text).strip()
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in flat:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            item = "".join(buf).strip().rstrip(",")
            if item:
                parts.append(item)
            buf = []
        else:
            buf.append(ch)
    item = "".join(buf).strip().rstrip(",")
    if item:
        parts.append(item)
    return parts


def wrap_list(text: str, width: int) -> list[str]:
    items = split_commas(text)
    if not items:
        return []
    if width < 8:
        width = 8
    lines: list[str] = []
    cur = ""
    for item in items:
        piece = item if not cur else f"{cur}, {item}"
        if not cur or len(piece) <= width:
            cur = piece
            continue
        lines.append(cur + ",")
        cur = item
    if cur:
        lines.append(cur)
    return lines


def render_fields(
    rows: list[tuple[str, str]],
    *,
    csr: Csr,
    columns: int,
    list_keys: frozenset[str] | None = None,
) -> str:
    """Format label/value rows to *columns*, wrapping values to the console width."""
    list_keys = list_keys or frozenset()
    present = [(k, v.strip()) for k, v in rows if v and str(v).strip()]
    if not present:
        return ""
    label_w = max(len(k) for k, _ in present)
    indent = label_w + 2
    value_w = max(16, columns - indent)
    lines: list[str] = []
    for key, val in present:
        label = f"{key}:"
        pad = " " * (label_w - len(key) + 1)
        styled = csr.wrap(label, csr.bold, csr.cyan) + pad
        if key in list_keys:
            wrapped = wrap_list(val, value_w)
        else:
            wrapped = wrap_text(val.replace("\n", " "), value_w)
        if not wrapped:
            continue
        lines.append(f"{styled}{wrapped[0]}")
        cont = " " * indent
        for extra in wrapped[1:]:
            lines.append(f"{cont}{extra}")
    return "\n".join(lines)


def human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KiB"
    return f"{n / (1024 * 1024):.1f} MiB"
