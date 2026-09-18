# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render text-FDM captures as ordered HTML (stdout/stderr highlight)."""

from __future__ import annotations

import html
from pathlib import Path

from fdm import CHAN_ERR, CHAN_OUT, iter_runs


def fdm_to_html(data: bytes) -> str:
    """Return HTML for FDM *data* preserving write order; channel-colored."""
    if not data:
        return '<pre class="fdm empty">(no output)</pre>'
    parts: list[str] = ['<pre class="fdm">']
    for channel, payload in iter_runs(data):
        text = payload.decode("utf-8", errors="replace")
        css = "out" if channel == CHAN_OUT else "err" if channel == CHAN_ERR else f"ch{channel}"
        # Split into lines but keep trailing content in order as spans
        parts.append(f'<span class="fdm-{css}">{html.escape(text)}</span>')
    parts.append("</pre>")
    return "".join(parts)


def fdm_file_to_html(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return '<pre class="fdm empty">(missing capture)</pre>'
    return fdm_to_html(data)
