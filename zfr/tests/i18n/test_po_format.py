# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for gettext .po no-wrap formatting."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.translate.po_format import (  # noqa: E402
    po_has_line_wrapping,
    po_no_wrap_text,
    read_po_text,
)


class PoFormatTests(unittest.TestCase):
    def test_detects_wrapped_catalog(self) -> None:
        wrapped = (
            'msgid "hello"\n'
            'msgstr "This is a long translation that gettext tools may split at the "\n'
            '"default column width"\n'
        )
        self.assertTrue(po_has_line_wrapping(wrapped))

    def test_no_wrap_single_line(self) -> None:
        plain = 'msgid "hello"\nmsgstr "short"\n'
        self.assertFalse(po_has_line_wrapping(plain))

    def test_read_po_text_latin1(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            po = Path(td) / "es_MX.po"
            po.write_bytes(
                b"# Spanish translations\n"
                b"# Traducciones al espa\xf1ol para el paquete\n"
                b'msgid "hello"\n'
                b'msgstr "hola"\n'
            )
            text = read_po_text(po)
            self.assertIn("español", text)

    def test_po_no_wrap_unwraps(self) -> None:
        wrapped = Path(__file__).resolve().parents[2] / "po" / "de.po"
        if not wrapped.is_file():
            self.skipTest("po/de.po missing")
        text = wrapped.read_text(encoding="utf-8")
        unwrapped = po_no_wrap_text(text)
        self.assertFalse(po_has_line_wrapping(unwrapped))


if __name__ == "__main__":
    unittest.main()
