# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for build-time derived locale Meson integration."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.i18n.meson import ensure_po_meson_derive  # noqa: E402
from zfr_lib.translate.po_files import catalog_locales, derived_build_locales  # noqa: E402


class I18nMesonDeriveTests(unittest.TestCase):
    def test_ensure_po_meson_derive_writes_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "po").mkdir()
            written = ensure_po_meson_derive(root)
            self.assertEqual(written, ["po/meson.build"])
            text = (root / "po" / "meson.build").read_text(encoding="utf-8")
            self.assertIn("zfr: i18n-derive-begin", text)
            self.assertIn("data_dirs: _po_src", text)
            self.assertIn("'--compile-mo'", text)
            self.assertIn("project_source_root", text)
            self.assertIn("add_install_script", text)
            self.assertIn("MESON_INSTALL_DESTDIR_PREFIX", text)
            self.assertIn("meson.project_name()", text)
            self.assertIn(r"split('\n')", text)

    def test_ensure_po_meson_derive_upgrades_incomplete_hook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            po = root / "po"
            po.mkdir()
            (po / "meson.build").write_text(
                "i18n = import('i18n')\n\n"
                "# zfr: i18n-derive-begin\n"
                "custom_target('i18n-derive', command: ['true'], "
                "output: 'i18n-derive.stamp')\n"
                "# zfr: i18n-derive-end\n\n"
                "i18n.gettext('demo', data_dirs: 'po', install: true)\n",
                encoding="utf-8",
            )
            written = ensure_po_meson_derive(root)
            self.assertEqual(written, ["po/meson.build"])
            text = (po / "meson.build").read_text(encoding="utf-8")
            self.assertIn("add_install_script", text)
            self.assertIn("--compile-mo", text)
            self.assertIn("MESON_INSTALL_DESTDIR_PREFIX", text)

    def test_catalog_locales_includes_derived(self) -> None:
        root = Path(__file__).resolve().parents[2]
        derived = derived_build_locales(root)
        self.assertIn("en_GB", derived)
        catalogs = catalog_locales(root)
        self.assertIn("de", catalogs)
        self.assertIn("en_GB", catalogs)


if __name__ == "__main__":
    unittest.main()
