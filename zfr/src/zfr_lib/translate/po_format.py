# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext .po formatting helpers (no line wrapping)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# Continuation string after a wrapped segment (previous line ends with `"` not `\n"`).
_WRAP_CONT_RE = re.compile(
    r'^"[^"\\]*(?:\\.[^"\\]*)*"[^\\]\n"',
    re.MULTILINE,
)


def po_has_line_wrapping(text: str) -> bool:
    """True when catalog uses gettext line wrapping (split long strings across lines)."""
    if _WRAP_CONT_RE.search(text):
        return True
    if shutil.which("msgcat") is None:
        return False
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".po", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(text)
        tmp_path = tmp.name
    try:
        proc = subprocess.run(
            ["msgcat", "--no-wrap", "-o", "-", tmp_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return False
        return proc.stdout != text
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def po_no_wrap_text(text: str) -> str:
    """Return *text* with gettext line wrapping removed."""
    if not po_has_line_wrapping(text):
        return text
    msgcat = shutil.which("msgcat")
    if msgcat is None:
        return text
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".po", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(text)
        src = tmp.name
    try:
        proc = subprocess.run(
            [msgcat, "--no-wrap", "-o", "-", src],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return text
        out = proc.stdout
        if not out.endswith("\n") and text.endswith("\n"):
            out += "\n"
        return out
    finally:
        Path(src).unlink(missing_ok=True)


def po_no_wrap_file(path: Path) -> bool:
    """Rewrite *path* without line wrapping. Returns True when changed."""
    original = path.read_text(encoding="utf-8")
    updated = po_no_wrap_text(original)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def po_no_wrap_tree(po_dir: Path) -> list[str]:
    """Run ``msgcat --no-wrap`` on every ``*.po`` under *po_dir*. Returns changed paths."""
    changed: list[str] = []
    if not po_dir.is_dir():
        return changed
    for po in sorted(po_dir.glob("*.po")):
        if po_no_wrap_file(po):
            changed.append(str(po))
    return changed
