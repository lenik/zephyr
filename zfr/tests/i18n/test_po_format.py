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
        translated, total, copies, empty = catalog_translation_stats(
            body, english_locale=False
        )
        self.assertEqual(total, 3)
        self.assertEqual(translated, 1)
        self.assertEqual(copies, 1)
        self.assertEqual(empty, 1)
        self.assertAlmostEqual(catalog_completion_ratio(body), 1 / 3)
        # Packaging field literal: msgstr == msgid counts as translated.
        from zfr_lib.translate.po_files import is_keep_english_msgid

        self.assertTrue(is_keep_english_msgid("Architecture: all"))
        self.assertFalse(is_keep_english_msgid("  [derived]"))
        lit = (
            'msgid ""\n'
            'msgstr "Content-Type: text/plain; charset=UTF-8\\n"\n'
            "\n"
            'msgid "Architecture: all"\n'
            'msgstr "Architecture: all"\n'
        )
        t3, tot3, c3, e3 = catalog_translation_stats(lit, english_locale=False)
        self.assertEqual((t3, tot3, c3, e3), (1, 1, 0, 0))
        # English variants may keep msgstr == msgid.
        t2, _tot2, c2, e2 = catalog_translation_stats(body, english_locale=True)
        self.assertEqual(t2, 2)
        self.assertEqual(c2, 0)
        self.assertEqual(e2, 1)
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
        translated, total, _copies, empty = catalog_translation_stats(body)
        self.assertEqual(total, 2)
        self.assertEqual(translated, 1)
        self.assertEqual(empty, 0)

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
            ph = [f for f in findings if f.code == "i18n.po.placeholder"]
            self.assertTrue(ph)
            self.assertEqual(ph[0].severity, "warn")

    def test_i18n_lint_warns_on_placeholder_even_when_mostly_done(self) -> None:
        import tempfile

        from zfr_lib.lint.i18n_check import check_i18n

        with tempfile.TemporaryDirectory(prefix="zfr-po-ph-") as tmp:
            root = Path(tmp)
            po = root / "po"
            po.mkdir()
            (po / "LINGUAS").write_text("de\n", encoding="utf-8")
            lines = [
                'msgid ""\n',
                'msgstr "Content-Type: text/plain; charset=UTF-8\\n"\n',
                "\n",
            ]
            for i in range(8):
                lines.append(f'msgid "msg{i}"\nmsgstr "übersetzt{i}"\n\n')
            lines.append('msgid "copy"\nmsgstr "copy"\n\n')
            lines.append('msgid "blank"\nmsgstr ""\n')
            (po / "de.po").write_text("".join(lines), encoding="utf-8")
            findings = check_i18n(root, "app", l10n_level="L1")
            quals = [f for f in findings if f.code == "i18n.po.quality"]
            self.assertTrue(quals)
            self.assertEqual(quals[0].severity, "ok")
            ph = [f for f in findings if f.code == "i18n.po.placeholder"]
            self.assertTrue(ph)
            self.assertEqual(ph[0].severity, "warn")
            self.assertIn("omitted", ph[0].message)
            self.assertIn("empty", ph[0].message)

    def test_i18n_lint_skips_keep_english_field_literals(self) -> None:
        import tempfile

        from zfr_lib.lint.i18n_check import check_i18n

        with tempfile.TemporaryDirectory(prefix="zfr-po-keep-") as tmp:
            root = Path(tmp)
            po = root / "po"
            po.mkdir()
            (po / "LINGUAS").write_text("de\nzh_CN\n", encoding="utf-8")
            header = (
                'msgid ""\n'
                'msgstr "Content-Type: text/plain; charset=UTF-8\\n"\n'
                "\n"
            )
            # zh_CN leave Architecture: all in English; translate the prose tag.
            (po / "zh_CN.po").write_text(
                header
                + 'msgid "Architecture: all"\nmsgstr "Architecture: all"\n\n'
                + 'msgid "  [derived]"\nmsgstr "  [派生]"\n',
                encoding="utf-8",
            )
            # de: same keep-English + omit the prose tag.
            (po / "de.po").write_text(
                header
                + 'msgid "Architecture: all"\nmsgstr "Architecture: all"\n\n'
                + 'msgid "  [derived]"\nmsgstr "  [derived]"\n',
                encoding="utf-8",
            )
            findings = check_i18n(root, "app", l10n_level="L1")
            ph = [f for f in findings if f.code == "i18n.po.placeholder"]
            self.assertTrue(ph)
            self.assertIn("de.po", ph[0].message)
            self.assertIn("omitted", ph[0].message)
            # Only the prose omission counts — not Architecture: all.
            self.assertRegex(ph[0].message, r"1 omitted")
            self.assertNotIn("zh_CN.po", ph[0].message)


if __name__ == "__main__":
    unittest.main()
