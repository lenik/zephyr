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


class PoQualityStatsTests(unittest.TestCase):
    def test_msgid_copy_counts_untranslated(self) -> None:
        from zfr_lib.translate.po_files import (
            catalog_completion_ratio,
            catalog_translation_stats,
            is_english_locale,
        )

        body = (
            'msgid ""\n'
            'msgstr "Content-Type: text/plain; charset=UTF-8\\n"\n'
            "\n"
            'msgid "Hello"\n'
            'msgstr "Hello"\n'
            "\n"
            'msgid "World"\n'
            'msgstr ""\n'
            "\n"
            'msgid "X"\n'
            'msgstr "Y"\n'
        )
        translated, total, copies = catalog_translation_stats(body, english_locale=False)
        self.assertEqual(total, 3)
        self.assertEqual(translated, 1)
        self.assertEqual(copies, 1)
        self.assertAlmostEqual(catalog_completion_ratio(body), 1 / 3)
        # English variants may keep msgstr == msgid.
        t2, _tot2, c2 = catalog_translation_stats(body, english_locale=True)
        self.assertEqual(t2, 2)
        self.assertEqual(c2, 0)
        self.assertTrue(is_english_locale("en_AU"))
        self.assertTrue(is_english_locale("en_GB"))
        self.assertFalse(is_english_locale("de"))

    def test_fuzzy_counts_untranslated(self) -> None:
        from zfr_lib.translate.po_files import catalog_translation_stats

        body = (
            'msgid "A"\n'
            'msgstr "a"\n'
            "\n"
            "#, fuzzy\n"
            'msgid "B"\n'
            'msgstr "b"\n'
        )
        translated, total, _copies = catalog_translation_stats(body)
        self.assertEqual(total, 2)
        self.assertEqual(translated, 1)

    def test_i18n_lint_warns_on_low_completion(self) -> None:
        import tempfile

        from zfr_lib.lint.i18n_check import check_i18n

        with tempfile.TemporaryDirectory(prefix="zfr-po-qual-") as tmp:
            root = Path(tmp)
            po = root / "po"
            po.mkdir()
            (po / "LINGUAS").write_text("fr\n", encoding="utf-8")
            # 1 real translation out of 10 → 10% (≤20%).
            lines = [
                'msgid ""\n',
                'msgstr "Content-Type: text/plain; charset=UTF-8\\n"\n',
                "\n",
            ]
            for i in range(9):
                lines.append(f'msgid "msg{i}"\nmsgstr "msg{i}"\n\n')
            lines.append('msgid "ok"\nmsgstr "d\'accord"\n')
            (po / "fr.po").write_text("".join(lines), encoding="utf-8")
            findings = check_i18n(root, "app", l10n_level="L1")
            quals = [f for f in findings if f.code == "i18n.po.quality"]
            self.assertTrue(quals)
            self.assertEqual(quals[0].severity, "warn")
            self.assertIn("poedit", (quals[0].fix or "").lower())


if __name__ == "__main__":
    unittest.main()
