# SPDX-License-Identifier: AGPL-3.0-or-later
"""translate color formatting tests."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import ROOT, ZEPHYR, add_src_to_path

add_src_to_path()

from zfr_lib.translate.fmt import locale_fg, locale_hue, paint_key, stripe_fg


class TranslateFmtTests(unittest.TestCase):
    def test_locale_hue_stable(self) -> None:
        self.assertEqual(locale_hue("fr"), locale_hue("fr"))
        self.assertNotEqual(locale_hue("fr"), locale_hue("de"))

    def test_locale_fg_consistent_per_locale(self) -> None:
        self.assertEqual(locale_fg("zh_CN", on=True), locale_fg("zh_CN", on=True))
        self.assertNotEqual(locale_fg("zh_CN", on=True), locale_fg("zh_TW", on=True))

    def test_stripe_alternates(self) -> None:
        self.assertNotEqual(stripe_fg(0, on=True), stripe_fg(1, on=True))
        self.assertEqual(stripe_fg(0, on=False), "")

    def test_paint_key_off_when_disabled(self) -> None:
        self.assertEqual(paint_key("hello", on=False), "hello")
        self.assertIn("\033", paint_key("hello", on=True))


class TranslateColorCliTests(unittest.TestCase):
    def test_color_never_plain(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-k", "-c", "never", "-m", "validate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("validate", proc.stdout)
        self.assertNotIn("\033[", proc.stdout)

    def test_color_always_keys_striped(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "t", "-k", "-c", "always", "-m", "validate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("\033[", proc.stdout)

    def test_color_always_match_distinct_key_and_locale(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(ZEPHYR),
                "t",
                "-m",
                "manage implemented",
                "-l",
                "fr",
                "-c",
                "always",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("\033[", proc.stdout)
        self.assertIn("fr (fr)", proc.stdout)
        self.assertIn("manage implemented gettext locales", proc.stdout)
        self.assertNotIn(" => ", proc.stdout)


if __name__ == "__main__":
    unittest.main()
