# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr i18n / translate command tests."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import ROOT, ZEPHYR, _env, add_src_to_path

add_src_to_path()


class LocaleTranslateCommandTests(unittest.TestCase):
    def test_translate_keys(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-k", "-m", "validate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("validate", proc.stdout)
        self.assertNotIn(" => ", proc.stdout)

    def test_translate_match_case_insensitive(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-k", "-m", "VALIDATE"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("validate", proc.stdout)

    def test_translate_match_case_sensitive(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-k", "-M", "VALIDATE"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("validate\n", proc.stdout + "\n")

    def test_translate_match_entire(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-k", "-m", "error", "-E"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("error\n", proc.stdout + "\n")

        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-k", "-m", "err", "-E"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("error\n", proc.stdout + "\n")

    def test_translate_match(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-m", "manage implemented", "-l", "fr"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("manage implemented gettext locales", proc.stdout)
        self.assertIn("fr (fr)", proc.stdout)
        self.assertNotIn(" => ", proc.stdout)

    def test_translate_search(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-s", "Run", "-l", "ar"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ar (ar)", proc.stdout)
        self.assertNotIn(" => ", proc.stdout)

    def test_translate_prefix_t(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-l", "de", "validate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("de (de):", proc.stdout)

    def test_i18n_lists_implemented(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "i18n", "-a"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("zh-CN (zh_CN)", proc.stdout)
        self.assertIn("es-419 (es)", proc.stdout)

    def test_translate_all_locales(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "translate", "validate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("zh-CN (zh_CN):", proc.stdout)
        self.assertGreaterEqual(len(proc.stdout.strip().splitlines()), 5)


if __name__ == "__main__":
    unittest.main()
