# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locale tier and fallback matrix tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.l10n import (  # noqa: E402
    DERIVE_PARENT,
    L10N_LEVELS,
    TIER_I,
    TIER_II,
    TIER_III,
    LOCALE_TIER_LABEL,
    fallback_chain,
    format_locale_display,
    normalize_locale,
    resolve_present_locale,
)
from zfr_lib.i18n.builder import opencc_convert, _which_opencc  # noqa: E402


class L10nTierTests(unittest.TestCase):
    def test_l10n_levels_are_tier_primaries(self) -> None:
        self.assertEqual(L10N_LEVELS["L1"], TIER_I)
        self.assertEqual(L10N_LEVELS["L2"], TIER_I + TIER_II)
        self.assertEqual(L10N_LEVELS["L3"], TIER_I + TIER_II + TIER_III)

    def test_normalize_bcp47_and_legacy(self) -> None:
        self.assertEqual(normalize_locale("en-US"), "en")
        self.assertEqual(normalize_locale("es-419"), "es_MX")
        self.assertEqual(normalize_locale("es"), "es_MX")
        self.assertEqual(normalize_locale("pt"), "pt_BR")
        self.assertEqual(normalize_locale("zh-CN"), "zh_CN")

    def test_fallback_chain_zh_hk(self) -> None:
        self.assertEqual(fallback_chain("zh_HK")[:2], ("zh_TW", "zh_CN"))
        self.assertIn("en", fallback_chain("zh_HK"))

    def test_fallback_chain_es_es(self) -> None:
        self.assertEqual(fallback_chain("es_ES"), ("es_MX", "en"))

    def test_legacy_alias_resolves_present(self) -> None:
        present = {"es", "pt", "de"}
        self.assertEqual(resolve_present_locale("es_MX", present), "es")
        self.assertEqual(resolve_present_locale("pt_BR", present), "pt")

    def test_derive_parent_zh_tw(self) -> None:
        self.assertEqual(DERIVE_PARENT["zh_TW"], "zh_CN")
        self.assertEqual(DERIVE_PARENT["zh_HK"], "zh_TW")

    @unittest.skipUnless(_which_opencc() is not None, "opencc CLI not installed")
    def test_opencc_simplified_to_traditional(self) -> None:
        out = opencc_convert("软件", "opencc_s2t")
        self.assertIn("軟", out)

    def test_opencc_unavailable_passthrough(self) -> None:
        """When the CLI is missing, conversion is a no-op (not an error)."""
        if _which_opencc() is not None:
            self.skipTest("opencc is installed")
        self.assertEqual(opencc_convert("软件", "opencc_s2t"), "软件")

    def test_tier_label_format(self) -> None:
        self.assertEqual(LOCALE_TIER_LABEL["sv"], "3.1")
        self.assertEqual(LOCALE_TIER_LABEL["es_MX"], "1.1")

    def test_format_locale_display_es_mx(self) -> None:
        self.assertEqual(format_locale_display("es"), "es-419 (es)")
        self.assertEqual(format_locale_display("es_MX"), "es-419 (es_MX)")

    def test_derive_skips_explicit_linguas_locale(self) -> None:
        import tempfile

        from zfr_lib.i18n.builder import default_build_po_dir, derive_locales

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            po = root / "po"
            po.mkdir()
            (po / "zh_CN.po").write_text(
                'msgid ""\nmsgstr ""\nmsgid "x"\nmsgstr "y"\n',
                encoding="utf-8",
            )
            (po / "LINGUAS").write_text("zh_CN\nzh_TW\n", encoding="utf-8")
            out = default_build_po_dir(root)
            self.assertEqual(
                derive_locales(root, po_dir=out, locales=("zh_TW",), skip_explicit=True),
                [],
            )
            (po / "LINGUAS").write_text("zh_CN\n", encoding="utf-8")
            written = derive_locales(root, po_dir=out, locales=("zh_TW",), skip_explicit=True)
            self.assertEqual(len(written), 1)
            self.assertTrue(written[0].endswith("zh_TW.po"))
            body = (out / "zh_TW.po").read_text(encoding="utf-8")
            self.assertIn("# Derived-From: zh_CN", body)
            self.assertIn("# Derived-Method: opencc_s2t", body)
            self.assertFalse((po / "zh_TW.po").exists())

    def test_derive_writes_only_to_build_dir(self) -> None:
        import tempfile
        import time

        from zfr_lib.i18n.builder import (
            _dest_fresh,
            default_build_po_dir,
            derive_locales,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            po = root / "po"
            po.mkdir()
            (po / "zh_CN.po").write_text(
                'msgid ""\nmsgstr ""\nmsgid "软件"\nmsgstr "软件"\n',
                encoding="utf-8",
            )
            (po / "LINGUAS").write_text("zh_CN\n", encoding="utf-8")
            out = default_build_po_dir(root)
            derive_locales(root, po_dir=out, locales=("zh_TW",))
            self.assertTrue((out / "zh_TW.po").is_file())
            self.assertFalse((po / "zh_TW.po").exists())

            src = po / "zh_CN.po"
            self.assertTrue(_dest_fresh(out / "zh_TW.po", src))
            written = derive_locales(root, po_dir=out, locales=("zh_TW",))
            self.assertEqual(written, [])
            # Ensure the parent catalog mtime advances past the derived file
            # (tmpfs can coalesce same-tick writes).
            time.sleep(0.02)
            (po / "zh_CN.po").write_text(
                (po / "zh_CN.po").read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            written = derive_locales(root, po_dir=out, locales=("zh_TW",))
            self.assertEqual(len(written), 1)

    def test_compile_derived_mo_skips_fresh(self) -> None:
        import tempfile
        import time

        from zfr_lib.i18n.builder import compile_derived_mo, derive_locales

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            po = root / "po"
            po.mkdir()
            (po / "zh_CN.po").write_text(
                'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n'
                'msgid "软件"\nmsgstr "软件"\n',
                encoding="utf-8",
            )
            (po / "LINGUAS").write_text("zh_CN\n", encoding="utf-8")
            out = root / "build" / "po"
            derive_locales(root, po_dir=out, locales=("zh_TW",))
            first = compile_derived_mo(out, "demo")
            self.assertEqual(len(first), 1)
            time.sleep(0.01)
            second = compile_derived_mo(out, "demo")
            self.assertEqual(second, [])
            po_path = out / "zh_TW.po"
            po_path.write_text(po_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            third = compile_derived_mo(out, "demo")
            self.assertEqual(len(third), 1)


if __name__ == "__main__":
    unittest.main()
