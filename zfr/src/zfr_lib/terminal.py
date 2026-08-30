# SPDX-License-Identifier: AGPL-3.0-or-later
"""Terminal and session context helpers."""

from __future__ import annotations

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


def default_lint_style_info() -> bool:
    """Default for zfr lint style-contract blurbs (-i/--info).

    On for non-interactive stdout (pipes, CI) and for AI-integrated terminals
    (Cursor, VS Code, Windsurf, …). Off for a plain interactive shell TTY.
    """
    if not stdout_is_interactive():
        return True
    return is_ai_terminal_context()
