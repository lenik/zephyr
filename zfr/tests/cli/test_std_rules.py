# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered lint/ize rule registry tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import ROOT, ZEPHYR, _env, add_src_to_path

add_src_to_path()

from zfr_lib.lint.filtering import filter_findings
from zfr_lib.lint.finding import Finding
from zfr_lib.std import lint_rule_id, render_std_help, render_std_table
from zfr_lib.std.lint_rules import LINT_RULES
from zfr_lib.std.ize_rules import IZE_RULES


class StdRuleTests(unittest.TestCase):
    def test_lint_rule_lookup_exact(self) -> None:
        self.assertEqual(lint_rule_id("rpm.missing"), "ZL026")

    def test_lint_rule_lookup_pattern(self) -> None:
        self.assertEqual(lint_rule_id("layout.meson.build"), "ZL003")
        self.assertEqual(lint_rule_id("debian.build-depends.meson"), "ZL008")
        self.assertEqual(lint_rule_id("readme.placeholder.README.md"), "ZL080")

    def test_ize_rule_lookup(self) -> None:
        self.assertEqual(IZE_RULES.rule_id("ize.rpm"), "ZI013")

    def test_by_id_accepts_numeric(self) -> None:
        self.assertEqual(LINT_RULES.by_id("26").id, "ZL026")
        self.assertEqual(IZE_RULES.by_id("15").id, "ZI015")

    def test_filter_uncheck_by_id(self) -> None:
        findings = [
            Finding("note", "rpm.missing", "no spec", "rpm/"),
            Finding("ok", "source.size", "fine"),
        ]
        out = filter_findings(findings, ["ZL026"])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].code, "source.size")

    def test_filter_uncheck_by_code(self) -> None:
        findings = [Finding("note", "rpm.missing", "no spec", "rpm/")]
        self.assertEqual(filter_findings(findings, ["rpm.missing"]), [])

    def test_list_std_table_covers_all_rules(self) -> None:
        lint_tbl = render_std_table(LINT_RULES.all_rules())
        ize_tbl = render_std_table(IZE_RULES.all_rules())
        for rule in LINT_RULES.all_rules():
            self.assertIn(rule.id, lint_tbl)
            self.assertIn(rule.code, lint_tbl)
        for rule in IZE_RULES.all_rules():
            self.assertIn(rule.id, ize_tbl)

    def test_help_std_text(self) -> None:
        rule = LINT_RULES.by_id("ZL026")
        assert rule is not None
        text = render_std_help(rule, command="lint")
        self.assertIn("ZL026", text)
        self.assertIn("rpm.missing", text)
        self.assertIn("zfr lint -u ZL026", text)


class StdRuleCliTests(unittest.TestCase):
    def test_lint_shows_rule_id(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "lint", "-v", "--color", "never"],
            cwd=ROOT,
            env=_env(),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout, r"\bZL\d{3}\b")

    def test_lint_list_std(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "lint", "-L"],
            cwd=ROOT,
            env=_env(),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ZL001", proc.stdout)
        self.assertIn("source.long", proc.stdout)

    def test_ize_help_std(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "ize", "-H", "15"],
            cwd=ROOT,
            env=_env(),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ZI015", proc.stdout)
        self.assertIn("ize.i18n.derive", proc.stdout)

    def test_lint_uncheck_hides_rule(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-lint-uncheck-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "debian").mkdir()
            (root / "debian" / "control").write_text(
                "Source: demo\nBuild-Depends: debhelper-compat (= 13)\n\n"
                "Package: demo\nArchitecture: all\nDescription: demo\n",
                encoding="utf-8",
            )
            (root / "meson.build").write_text("project('demo')\n", encoding="utf-8")
            env = _env()
            base = subprocess.run(
                [sys.executable, str(ZEPHYR), "lint", "--color", "never"],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertIn("ZL026", base.stdout)
            suppressed = subprocess.run(
                [
                    sys.executable,
                    str(ZEPHYR),
                    "lint",
                    "-u",
                    "ZL026",
                    "--color",
                    "never",
                ],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotIn("rpm.missing", suppressed.stdout)


if __name__ == "__main__":
    unittest.main()
