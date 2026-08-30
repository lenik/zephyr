# SPDX-License-Identifier: AGPL-3.0-or-later
"""Coverage for every zfr subcommand, wrapper, and --version source."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import REPO, ROOT, TOOLS, ZEPHYR, _env, run_zephyr, add_src_to_path

add_src_to_path()

WRAPPERS = (
    "zfr-create",
    "zfr-rename",
    "zfr-add",
    "zfr-remove",
    "zfr-about",
    "zfr-version",
    "zfr-lint",
    "zfr-shape",
    "zfr-dist",
    "zfr-ize",
    "zfr-i18n",
    "zfr-translate",
    "zfr-release",
)

SUBCOMMANDS = (
    "create",
    "rename",
    "add",
    "remove",
    "about",
    "version",
    "lint",
    "shape",
    "dist",
    "release",
    "ize",
    "i18n",
    "translate",
    "detect",
    "help",
)


class ZephyrDispatcherTests(unittest.TestCase):
    def test_version_not_hardcoded_in_src(self) -> None:
        text = (TOOLS / "zfr").read_text(encoding="utf-8")
        self.assertNotRegex(text, r'__version__\s*=\s*["\']\d+\.\d+')
        self.assertIn("cli_version", text)

    def test_cli_version_matches_runtime(self) -> None:
        sys.path.insert(0, str(TOOLS))
        from zfr_lib import cli_version

        proc = run_zephyr("--version")
        self.assertIn(cli_version(), proc.stdout)

    def test_every_subcommand_help(self) -> None:
        for name in SUBCOMMANDS:
            with self.subTest(name=name):
                proc = run_zephyr(name, "-h")
                self.assertEqual(proc.returncode, 0)
                self.assertTrue(proc.stdout.strip())

    def test_every_wrapper_help(self) -> None:
        for name in WRAPPERS:
            with self.subTest(name=name):
                proc = subprocess.run(
                    [sys.executable, str(TOOLS / name), "--help"],
                    env=_env(),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertTrue(proc.stdout.strip())

    def test_unknown_command(self) -> None:
        proc = run_zephyr("not-a-command", check=False)
        self.assertNotEqual(proc.returncode, 0)

    def test_detect_every_language_template(self) -> None:
        sys.path.insert(0, str(TOOLS))
        from zfr_lib import LANGS

        for lang in LANGS:
            d = REPO / lang
            if not (d / "meson.build").is_file():
                continue
            with self.subTest(lang=lang):
                proc = run_zephyr("detect", cwd=d)
                self.assertEqual(proc.stdout.strip(), lang)

    def test_about_debian_and_rpm_flags(self) -> None:
        about = run_zephyr("about", cwd=ROOT)
        self.assertIn("zephyr", about.stdout.lower())
        deb = run_zephyr("about", "-d", cwd=ROOT)
        self.assertTrue("Source" in deb.stdout or "Package" in deb.stdout or "Debian" in deb.stdout)
        rpm = run_zephyr("about", "-r", cwd=ROOT)
        self.assertTrue(rpm.stdout.strip())

    def test_version_sources(self) -> None:
        v = run_zephyr("version", cwd=ROOT)
        self.assertTrue(v.stdout.strip())
        g = run_zephyr("version", "-g", cwd=ROOT)
        self.assertTrue(g.stdout.strip())
        c = run_zephyr("version", "-c", cwd=ROOT)
        self.assertRegex(c.stdout.strip(), r"^\d")
        r = run_zephyr("version", "-r", cwd=ROOT)
        self.assertNotIn("-", r.stdout.strip())

    def test_lint_flags(self) -> None:
        v = run_zephyr("lint", "-v", "--color", "never", cwd=ROOT, check=False)
        self.assertIn("zfr lint", v.stdout)
        q = run_zephyr("lint", "-q", cwd=ROOT, check=False)
        self.assertIn("zfr lint", q.stdout)
        s = run_zephyr("lint", "--strict", cwd=ROOT, check=False)
        self.assertIn(s.returncode, (0, 1))
        l0 = run_zephyr("lint", "-l", "0", "--color", "never", cwd=ROOT, check=False)
        self.assertIn("zfr lint", l0.stdout)
        self.assertIn("L0", l0.stdout)
        l2 = run_zephyr("lint", "-l", "2", "--color", "never", cwd=ROOT, check=False)
        self.assertIn("L2", l2.stdout)
        bad = run_zephyr("lint", "-l", "9", cwd=ROOT, check=False)
        self.assertNotEqual(bad.returncode, 0)

    def test_shape_threshold(self) -> None:
        b = run_zephyr("shape", "-b", "--threshold", "1", "-v", cwd=ROOT)
        self.assertEqual(b.stdout.strip(), "1")
        self.assertIn("# packagedir=", b.stderr)

    def test_ize_no_man_no_subst_dry_run(self) -> None:
        proc = run_zephyr(
            "ize", "-n", "--no-man", "--no-subst", cwd=REPO / "bash"
        )
        self.assertIn("zfr ize", proc.stdout)
        self.assertIn("dry-run", proc.stdout)

    def test_create_python_and_about(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-py-") as tmp:
            dest = Path(tmp) / "py_demo"
            run_zephyr("create", "-l", "python", "-1", "0.0.1", str(dest), "hello")
            self.assertTrue((dest / "meson.build").is_file())
            det = run_zephyr("detect", cwd=dest)
            self.assertEqual(det.stdout.strip(), "python")
            about = run_zephyr("about", cwd=dest)
            self.assertIn("py_demo", about.stdout)

    def test_release_help_and_argv(self) -> None:
        proc = run_zephyr("release", "-h")
        self.assertIn("gh-makerelease", proc.stdout)
        from zfr_lib.release import add_release_arguments, compose_makerelease_argv

        p = argparse.ArgumentParser()
        add_release_arguments(p)
        ns = p.parse_args(["-l", "--unsigned"])
        argv = compose_makerelease_argv(ns)
        self.assertIn("--local", argv)
        self.assertIn("--unsigned", argv)


class ZephyrLangScoreTests(unittest.TestCase):
    def test_score_langs_prefers_python_sources(self) -> None:
        sys.path.insert(0, str(TOOLS))
        from zfr_lib.lang import rank_langs

        with tempfile.TemporaryDirectory(prefix="zfr-score-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
            ranked = rank_langs(root)
            self.assertEqual(ranked[0][0], "python")
            self.assertGreater(ranked[0][1], 0)


if __name__ == "__main__":
    unittest.main()
