# SPDX-License-Identifier: AGPL-3.0-or-later
"""Terminal and session context helpers."""

from __future__ import annotations

import argparse
import os
import sys

# TERM_PROGRAM values seen in AI-integrated editors (lowercase for matching).
_AI_TERM_PROGRAMS = frozenset(
    {
        "cursor",
        "vscode",
        "visual studio code",
        "windsurf",
        "code",
    }
)


def stdout_is_interactive() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def is_ai_terminal_context() -> bool:
    """True when the session looks like an AI-agent integrated terminal."""
    prog = os.environ.get("TERM_PROGRAM", "").strip().lower()
    if prog in _AI_TERM_PROGRAMS or prog.startswith("cursor"):
        return True
    if os.environ.get("VSCODE_PID") or os.environ.get("VSCODE_GIT_IPC_HANDLE"):
        return True
    if os.environ.get("CURSOR_TRACE_ID") or os.environ.get("CURSOR_AGENT"):
        return True
    # Some builds only expose a Cursor/VS Code version string.
    ver = os.environ.get("TERM_PROGRAM_VERSION", "").strip().lower()
    if ver.startswith("cursor") or ver.startswith("vscode"):
        return True
    return False


def default_for_ai_purpose() -> bool:
    """Default for the global ``--for-ai-purpose`` flag.

    On when an AI-integrated editor is detected, or when stdout is
    non-interactive (pipes/CI) — the same situations where lint ``--info``
    defaults on unless the user overrides it.
    """
    if is_ai_terminal_context():
        return True
    if not stdout_is_interactive():
        return True
    return False


def resolve_for_ai_purpose(value: bool | None) -> bool:
    if value is not None:
        return bool(value)
    return default_for_ai_purpose()


def add_for_ai_purpose_arguments(parser: argparse.ArgumentParser) -> None:
    """Register global ``--for-ai-purpose`` / ``--no-for-ai-purpose``."""
    from .i18n import _

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--for-ai-purpose",
        dest="for_ai_purpose",
        action="store_true",
        help=_(
            "enable AI-oriented hints (default for AI terminals and non-interactive stdout)"
        ),
    )
    group.add_argument(
        "--no-for-ai-purpose",
        dest="for_ai_purpose",
        action="store_false",
        help=_("disable AI-oriented hints (default for a plain interactive shell)"),
    )
    parser.set_defaults(for_ai_purpose=None)


def default_lint_style_info() -> bool:
    """Default for zfr lint style-contract blurbs (-i/--info).

    On for non-interactive stdout (pipes, CI) and for AI-integrated terminals
    (Cursor, VS Code, Windsurf, …). Off for a plain interactive shell TTY.
    Aligns with ``default_for_ai_purpose``.
    """
    return default_for_ai_purpose()
