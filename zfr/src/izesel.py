# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr-izesel — interactive ize rule ignore / always toggles."""

from __future__ import annotations

import argparse
import curses
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from lib import find_project_dir
from cli import register_command
from cmd_options import IZE_OPTIONS_REL, load_option_tokens, options_path
from i18n import _
from std import IZE_RULES, StdRule

NAME = "izesel"
HELP = _("interactively select ize rules to ignore or force")
DESCRIPTION = _(
    "Open a TUI to toggle ize rule overrides for this project "
    "(.config/zfr/ize.options). Lists only rules that match this tree "
    "(plus any already overridden). "
    "States: default / always(enable override) / ignored. "
    "Space=default/ignored, Y=always, N/-=ignored, ~=invert, "
    "Ctrl+S save, Ctrl+D save&quit, Ctrl+Q quit."
)


class RuleState(str, Enum):
    DEFAULT = "default"
    ALWAYS = "always"
    IGNORED = "ignored"


_MARK = {
    RuleState.DEFAULT: " ",
    RuleState.ALWAYS: "*",
    RuleState.IGNORED: "-",
}

_SECTION_BEGIN = "# --- zfr-izesel rules ---"
_SECTION_END = "# --- end zfr-izesel ---"


@dataclass
class RuleRow:
    rule: StdRule
    state: RuleState


def _parse_rule_overrides(tokens: list[str]) -> dict[str, RuleState]:
    out: dict[str, RuleState] = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("-u", "--uncheck") and i + 1 < len(tokens):
            for piece in tokens[i + 1].split(","):
                piece = piece.strip()
                if not piece:
                    continue
                rule = IZE_RULES.by_id(piece)
                out[rule.id if rule else piece.upper()] = RuleState.IGNORED
            i += 2
            continue
        if tok in ("-a", "--always") and i + 1 < len(tokens):
            for piece in tokens[i + 1].split(","):
                piece = piece.strip()
                if not piece:
                    continue
                rule = IZE_RULES.by_id(piece)
                out[rule.id if rule else piece.upper()] = RuleState.ALWAYS
            i += 2
            continue
        if tok.startswith("--uncheck="):
            for piece in tok.split("=", 1)[1].split(","):
                piece = piece.strip()
                if piece:
                    rule = IZE_RULES.by_id(piece)
                    out[rule.id if rule else piece.upper()] = RuleState.IGNORED
        elif tok.startswith("--always="):
            for piece in tok.split("=", 1)[1].split(","):
                piece = piece.strip()
                if piece:
                    rule = IZE_RULES.by_id(piece)
                    out[rule.id if rule else piece.upper()] = RuleState.ALWAYS
        i += 1
    return out


def matching_ize_rule_ids(root: Path) -> set[str]:
    """Ize rule IDs that match at least one path under *root*."""
    from lint.scanner import scan_project, select_scheduled
    from lint.session import Session
    from lint.util import _role
    from std.ize_rules import all_ize_specs

    role = _role(root)
    try:
        from lib import detect_lang

        lang = detect_lang(root) if role != "meta" else "meta"
    except SystemExit:
        lang = "unknown"
    session = Session(root=root, lang=lang, role=role)
    specs = all_ize_specs()
    _f2r, r2f = scan_project(root, specs, session)
    return {spec.id for spec, _ in select_scheduled(specs, r2f, require_files=True)}


def load_rule_rows(root: Path) -> list[RuleRow]:
    overrides = _parse_rule_overrides(load_option_tokens(root, IZE_OPTIONS_REL))
    matched = matching_ize_rule_ids(root)
    rows: list[RuleRow] = []
    for rule in IZE_RULES.all_rules():
        if rule.id not in matched and rule.id not in overrides:
            continue
        rows.append(
            RuleRow(rule=rule, state=overrides.get(rule.id, RuleState.DEFAULT))
        )
    return rows


def _non_rule_option_lines(text: str) -> list[str]:
    lines_out: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == _SECTION_BEGIN:
            in_section = True
            continue
        if stripped == _SECTION_END:
            in_section = False
            continue
        if in_section:
            continue
        body = line.split("#", 1)[0].strip()
        if re.match(r"^(-u|--uncheck|-a|--always)\b", body):
            continue
        lines_out.append(line)
    return lines_out


def save_rule_rows(root: Path, rows: list[RuleRow]) -> Path:
    path = options_path(root, IZE_OPTIONS_REL)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    kept = _non_rule_option_lines(existing)
    ignored = [r.rule.id for r in rows if r.state == RuleState.IGNORED]
    always = [r.rule.id for r in rows if r.state == RuleState.ALWAYS]
    block = [_SECTION_BEGIN]
    if ignored:
        for i in range(0, len(ignored), 12):
            block.append(f"-u {','.join(ignored[i : i + 12])}")
    if always:
        for i in range(0, len(always), 12):
            block.append(f"--always {','.join(always[i : i + 12])}")
    if not ignored and not always:
        block.append("# (no rule overrides)")
    block.append(_SECTION_END)
    body = "\n".join(kept).rstrip()
    if body:
        body += "\n"
    body += "\n".join(block) + "\n"
    path.write_text(body, encoding="utf-8")
    return path


def _toggle_default_ignored(state: RuleState) -> RuleState:
    if state == RuleState.IGNORED:
        return RuleState.DEFAULT
    return RuleState.IGNORED


def run_izesel_tui(root: Path) -> int:
    if not sys.stdout.isatty() or not sys.stdin.isatty():
        print(_("zfr-izesel requires an interactive TTY"), file=sys.stderr)
        return 2

    rows = load_rule_rows(root)

    def _main(stdscr: curses.window) -> int:
        curses.curs_set(0)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        except curses.error:
            pass
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_RED, -1)

        idx = 0
        top = 0
        dirty = False
        flash = ""

        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            title = (
                "zfr-izesel  SPC toggle  Y always  N/- ignore  ~ invert  "
                "PgUp/PgDn  mouse  ^S save  ^D save&quit  ^Q quit"
            )
            try:
                stdscr.addnstr(0, 0, title[: max(0, w - 1)], max(0, w - 1), curses.A_BOLD)
            except curses.error:
                pass
            meta = (
                f"{root}  {IZE_OPTIONS_REL.as_posix()}  "
                f"{'*' if dirty else ' '}  {idx + 1}/{len(rows)}"
            )
            try:
                stdscr.addnstr(1, 0, meta[: max(0, w - 1)], max(0, w - 1))
            except curses.error:
                pass
            if flash:
                try:
                    stdscr.addnstr(2, 0, flash[: max(0, w - 1)], max(0, w - 1), curses.A_BOLD)
                except curses.error:
                    pass
                flash = ""

            list_top = 4
            visible = max(1, h - list_top - 1)
            if idx < top:
                top = idx
            if idx >= top + visible:
                top = idx - visible + 1

            for row_i in range(visible):
                ri = top + row_i
                if ri >= len(rows):
                    break
                row = rows[ri]
                mark = _MARK[row.state]
                line = f"[{mark}] {row.rule.id}  {row.rule.code}  {row.rule.title}"
                attr = curses.A_REVERSE if ri == idx else curses.A_NORMAL
                if curses.has_colors() and ri != idx:
                    if row.state == RuleState.ALWAYS:
                        attr |= curses.color_pair(1)
                    elif row.state == RuleState.IGNORED:
                        attr |= curses.color_pair(3)
                try:
                    stdscr.addnstr(
                        list_top + row_i, 0, line[: max(0, w - 1)], max(0, w - 1), attr
                    )
                except curses.error:
                    pass
            stdscr.refresh()

            ch = stdscr.getch()
            if ch in (curses.KEY_UP, ord("k")):
                idx = max(0, idx - 1)
            elif ch in (curses.KEY_DOWN, ord("j")):
                idx = min(len(rows) - 1, idx + 1)
            elif ch == curses.KEY_PPAGE:
                idx = max(0, idx - visible)
            elif ch == curses.KEY_NPAGE:
                idx = min(len(rows) - 1, idx + visible)
            elif ch == ord(" "):
                rows[idx].state = _toggle_default_ignored(rows[idx].state)
                dirty = True
            elif ch in (ord("Y"), ord("y")):
                rows[idx].state = RuleState.ALWAYS
                dirty = True
            elif ch in (ord("N"), ord("n"), ord("-")):
                rows[idx].state = RuleState.IGNORED
                dirty = True
            elif ch == ord("~"):
                for r in rows:
                    if r.state != RuleState.ALWAYS:
                        r.state = _toggle_default_ignored(r.state)
                dirty = True
            elif ch == curses.KEY_MOUSE:
                try:
                    _id, _x, y, _z, bstate = curses.getmouse()
                except curses.error:
                    continue
                if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED):
                    click_i = top + (y - list_top)
                    if 0 <= click_i < len(rows):
                        idx = click_i
                        rows[idx].state = _toggle_default_ignored(rows[idx].state)
                        dirty = True
            elif ch == 19:  # Ctrl+S
                path = save_rule_rows(root, rows)
                dirty = False
                flash = f"saved {path}"
            elif ch == 4:  # Ctrl+D
                save_rule_rows(root, rows)
                return 0
            elif ch in (17, 27):  # Ctrl+Q / ESC
                return 0
        return 0

    return int(curses.wrapper(_main) or 0)


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-C",
        "--directory",
        type=Path,
        default=None,
        help=_("project directory (default: walk from cwd)"),
    )


def run(args: argparse.Namespace) -> int:
    return run_izesel_tui(find_project_dir(getattr(args, "directory", None)))


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
