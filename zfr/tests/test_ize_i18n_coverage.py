# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for zfr ize i18n coverage steps."""

from __future__ import annotations

import unittest
from pathlib import Path

from ize.engine import Ize


class IzeI18nCoverageTests(unittest.TestCase):
    def _project(self, tmp: Path) -> Path:
        root = tmp / "proj"
        (root / "po").mkdir(parents=True)
        (root / "man").mkdir()
        (root / "po" / "LINGUAS").write_text("fr\nde\n", encoding="utf-8")
        (root / "po" / "proj.pot").write_text(
            'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
            'msgid "Hello"\nmsgstr ""\n',
            encoding="utf-8",
        )
        for loc in ("fr", "de"):
            (root / "po" / f"{loc}.po").write_text(
                'msgid ""\nmsgstr ""\n"Language: %s\\n"\n\nmsgid "Hello"\nmsgstr "X"\n'
                % loc,
                encoding="utf-8",
            )
            (root / "man" / loc).mkdir()
            (root / "man" / loc / "tool.adoc").write_text(
                f"= tool(1)\n\n== NAME\n\ntool - {loc}\n",
                encoding="utf-8",
            )
        (root / "man" / "tool.adoc").write_text(
            "= tool(1)\n\n== NAME\n\ntool - English\n",
            encoding="utf-8",
        )
        return root

    def test_dry_run_reports_missing_l1_locales(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = self._project(Path(td))
            ize = Ize(root, lang="python", dry_run=True)
            ize.ensure_i18n_coverage()
            ize.ensure_man_locale_coverage()
            paths = {c.path for c in ize.changes}
            self.assertTrue(any(p.startswith("po/") and "ar" in p for p in paths))
            # ize no longer scaffolds man/<locale>/ copies.
            self.assertFalse(any(p.startswith("man/ar/") for p in paths))
            self.assertFalse((root / "man" / "ar" / "tool.adoc").exists())

    def test_apply_adds_linguas_po_not_man_scaffold(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = self._project(Path(td))
            ize = Ize(root, lang="python", dry_run=False)
            ize.ensure_i18n_coverage()
            ize.ensure_man_locale_coverage()
            linguas = (root / "po" / "LINGUAS").read_text(encoding="utf-8")
            self.assertIn("ar", linguas)
            self.assertTrue((root / "po" / "ar.po").is_file())
            self.assertFalse((root / "man" / "ar" / "tool.adoc").is_file())


if __name__ == "__main__":
    unittest.main()
