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
_CONTENT_TYPE_RE = re.compile(
    r'Content-Type:\s*text/plain;\s*charset=([^\s\\"]+)',
    re.IGNORECASE,
)
_CHARSET_LINE_RE = re.compile(
    r'^("Content-Type:\s*text/plain;\s*charset=)[^\s\\"]+',
    re.MULTILINE | re.IGNORECASE,
)


def read_po_text(path: Path) -> str:
    """Read a gettext catalog, honoring its declared charset when not UTF-8."""
    data = path.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    head = data[:4096].decode("latin-1", errors="replace")
    m = _CONTENT_TYPE_RE.search(head)
    if m:
        charset = m.group(1).strip()
        try:
            return data.decode(charset)
        except (LookupError, UnicodeDecodeError):
            pass
    return data.decode("latin-1")


def po_normalize_utf8(text: str) -> str:
    """Ensure gettext header declares UTF-8 charset."""
    return _CHARSET_LINE_RE.sub(r"\1UTF-8", text)


def po_prepare_utf8(text: str) -> str:
    """Remove line wrapping and normalize charset header to UTF-8."""
    return po_normalize_utf8(po_no_wrap_text(text))


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
    """Rewrite *path* as UTF-8 without line wrapping. Returns True when changed."""
    original_bytes = path.read_bytes()
    updated = po_prepare_utf8(read_po_text(path))
    new_bytes = updated.encode("utf-8")
    if new_bytes == original_bytes:
        return False
    path.write_bytes(new_bytes)
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
