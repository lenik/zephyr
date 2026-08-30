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
from zfr_lib.i18n.builder import opencc_convert  # noqa: E402


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

    def test_opencc_simplified_to_traditional(self) -> None:
        out = opencc_convert("软件", "opencc_s2t")
        self.assertIn("軟", out)

    def test_tier_label_format(self) -> None:
        self.assertEqual(LOCALE_TIER_LABEL["sv"], "3.1")
        self.assertEqual(LOCALE_TIER_LABEL["es_MX"], "1.1")

    def test_format_locale_display_es_mx(self) -> None:
        self.assertEqual(format_locale_display("es"), "es-419 (es)")
        self.assertEqual(format_locale_display("es_MX"), "es-419 (es_MX)")

    def test_derive_skips_explicit_linguas_locale(self) -> None:
        import tempfile

        from zfr_lib.i18n.builder import derive_locales

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            po = root / "po"
            po.mkdir()
            (po / "zh_CN.po").write_text(
                'msgid ""\nmsgstr ""\nmsgid "x"\nmsgstr "y"\n',
                encoding="utf-8",
            )
            (po / "LINGUAS").write_text("zh_CN\nzh_TW\n", encoding="utf-8")
            self.assertEqual(
                derive_locales(root, locales=("zh_TW",), skip_explicit=True),
                [],
            )
            (po / "LINGUAS").write_text("zh_CN\n", encoding="utf-8")
            written = derive_locales(root, locales=("zh_TW",), skip_explicit=True)
            self.assertEqual(written, ["po/zh_TW.po"])


if __name__ == "__main__":
    unittest.main()
