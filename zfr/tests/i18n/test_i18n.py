# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext catalogs and whole-document manpage translations."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import ROOT, TOOLS, ZEPHYR, _env, run_zephyr, add_src_to_path

add_src_to_path()

PO = ROOT / "po"
DOCS = ROOT / "docs"


def _linguas() -> list[str]:
    lines = (PO / "LINGUAS").read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def _po_untranslated(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    missing: list[str] = []
    blocks = re.split(r"\n(?=msgid )", text)
    for block in blocks[1:]:
        m = re.match(
            r"msgid ((?:\"(?:\\.|[^\"\\])*\"(?:\n)?)*)\nmsgstr ((?:\"(?:\\.|[^\"\\])*\"(?:\n)?)*)",
            block,
        )
        if not m:
            continue
        mid = "".join(re.findall(r'"((?:\\.|[^"\\])*)"', m.group(1)))
        ms = "".join(re.findall(r'"((?:\\.|[^"\\])*)"', m.group(2)))
        mid = mid.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
        ms = ms.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
        if mid and not ms:
            missing.append(mid[:60])
    return missing


class ZephyrGettextTests(unittest.TestCase):
    def test_linguas_covers_l2(self) -> None:
        sys.path.insert(0, str(TOOLS))
        from zfr_lib.l10n import L10N_LEVELS, resolve_present_locale

        present = set(_linguas())
        missing = [
            loc
            for loc in L10N_LEVELS["L2"]
            if resolve_present_locale(loc, present) is None
        ]
        self.assertEqual(
            missing,
            [],
            f"LINGUAS missing L2 primaries (via legacy/fallback): {missing}",
        )

    def test_every_catalog_complete(self) -> None:
        for loc in _linguas():
            po = PO / f"{loc}.po"
            with self.subTest(loc=loc):
                self.assertTrue(po.is_file(), po)
                missing = _po_untranslated(po)
                self.assertEqual(missing, [], f"{loc}: {missing[:5]}")
                proc = subprocess.run(
                    ["msgfmt", "-c", "-o", "/dev/null", str(po)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_help_zh_cn_and_de(self) -> None:
        for lang, needle in (("zh_CN", "模板助手"), ("de", "Vorlagen")):
            with self.subTest(lang=lang):
                env = _env()
                env["LANGUAGE"] = lang
                env["LANG"] = "C.UTF-8"
                env["LC_ALL"] = "C.UTF-8"
                # Force re-init in a fresh process.
                proc = subprocess.run(
                    [sys.executable, str(ZEPHYR), "-h"],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn(needle, proc.stdout)

    def test_lint_zh_cn_and_de(self) -> None:
        for lang, needles in (
            ("zh_CN", ("状态:", "错误=", "警告=")),
            ("de", ("Status:", "Fehler=", "Warnungen=")),
        ):
            with self.subTest(lang=lang):
                env = _env()
                env["LANGUAGE"] = lang
                env["LANG"] = "C.UTF-8"
                env["LC_ALL"] = "C.UTF-8"
                proc = subprocess.run(
                    [sys.executable, str(ZEPHYR), "lint", "--color", "never"],
                    env=env,
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertIn("zfr lint", proc.stdout)
                for needle in needles:
                    self.assertIn(needle, proc.stdout, proc.stdout[:500])


class ZephyrManpageTranslationTests(unittest.TestCase):
    def test_every_locale_has_whole_document_adoc(self) -> None:
        sys.path.insert(0, str(TOOLS))
        from zfr_lib.l10n import EN_MAN_NAME, L10N_LEVELS, resolve_present_locale

        english = (DOCS / "zfr.adoc").read_text(encoding="utf-8")
        self.assertIn("== Name", english)
        present = set(_linguas())
        required: set[str] = set(_linguas())
        for loc in L10N_LEVELS["L2"]:
            resolved = resolve_present_locale(loc, present) or loc
            required.add(resolved)
        for loc in sorted(required):
            path = DOCS / loc / "zfr.adoc"
            with self.subTest(loc=loc):
                self.assertTrue(path.is_file(), path)
                text = path.read_text(encoding="utf-8")
                self.assertIn("= zfr(1)", text)
                self.assertIn("== Synopsis", text)
                self.assertIn("*zfr* *create*", text)
                # Must be a real translation, not a copy of English Name.
                self.assertNotIn(
                    "zfr - multi-language CLI project templates and helper tools",
                    text,
                )
                self.assertNotIn(EN_MAN_NAME, text)

    def test_zh_cn_and_de_name_translated(self) -> None:
        zh = (DOCS / "zh_CN" / "zfr.adoc").read_text(encoding="utf-8")
        de = (DOCS / "de" / "zfr.adoc").read_text(encoding="utf-8")
        self.assertIn("多语言", zh)
        self.assertIn("Projektvorlagen", de)

    def test_no_po4a_man_catalogs(self) -> None:
        self.assertFalse((ROOT / "po4a.cfg").exists())
        self.assertFalse((PO / "man").exists())


if __name__ == "__main__":
    unittest.main()
