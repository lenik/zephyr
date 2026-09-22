# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for meson version subst / posync / scripts lint and lintsel IO."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from support import add_src_to_path

add_src_to_path()


class VersionSubstLintTests(unittest.TestCase):
    def test_ok_when_subst_and_used(self) -> None:
        from lint.scripts_check import check_version_subst

        with tempfile.TemporaryDirectory(prefix="zfr-vsubst-") as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text(
                "project('demo')\n"
                "cfg = configuration_data()\n"
                "cfg.set('VERSION', meson.project_version())\n",
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src" / "app.in").write_text("echo @VERSION@\n", encoding="utf-8")
            findings = check_version_subst(root, "app")
            self.assertTrue(any(f.severity == "ok" and f.code == "meson.version_subst" for f in findings))

    def test_warn_when_subst_unused(self) -> None:
        from lint.scripts_check import check_version_subst

        with tempfile.TemporaryDirectory(prefix="zfr-vsubst2-") as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text(
                "cfg.set_quoted('PROJECT_VERSION', meson.project_version())\n",
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src" / "main.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
            findings = check_version_subst(root, "app")
            self.assertTrue(any(f.severity == "warn" and f.code == "meson.version_subst" for f in findings))


class PosyncLintTests(unittest.TestCase):
    def test_warn_inline_posync(self) -> None:
        from lint.scripts_check import check_posync

        with tempfile.TemporaryDirectory(prefix="zfr-posync-") as tmp:
            root = Path(tmp)
            (root / "po").mkdir()
            (root / "meson.build").write_text(
                "run_target(\n"
                "    'posync',\n"
                "    command: [\n"
                "        'bash',\n"
                "        '-euc',\n"
                "        '''\n"
                "            cd po\n"
                "            xgettext ...\n"
                "        ''',\n"
                "    ],\n"
                ")\n",
                encoding="utf-8",
            )
            findings = check_posync(root, "app")
            self.assertTrue(any(f.code == "layout.posync" and f.severity == "warn" for f in findings))

    def test_ok_external_posync(self) -> None:
        from lint.scripts_check import check_posync

        with tempfile.TemporaryDirectory(prefix="zfr-posync-ok-") as tmp:
            root = Path(tmp)
            (root / "po").mkdir()
            (root / "scripts").mkdir()
            (root / "scripts" / "posync.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            (root / "meson.build").write_text(
                "run_target(\n"
                "    'posync',\n"
                "    command: [\n"
                "        'bash',\n"
                "        meson.project_source_root() / 'scripts' / 'posync.sh',\n"
                "    ],\n"
                ")\n",
                encoding="utf-8",
            )
            findings = check_posync(root, "app")
            self.assertTrue(any(f.code == "layout.posync" and f.severity == "ok" for f in findings))


class ScriptsLayoutLintTests(unittest.TestCase):
    def test_warn_root_deploy_sh(self) -> None:
        from lint.scripts_check import check_scripts_layout

        with tempfile.TemporaryDirectory(prefix="zfr-scripts-") as tmp:
            root = Path(tmp)
            (root / "deploy-prod.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            findings = check_scripts_layout(root, "app")
            self.assertTrue(any(f.code == "layout.scripts" and f.severity == "warn" for f in findings))


class LintselIOTests(unittest.TestCase):
    def test_save_and_reload(self) -> None:
        from lintsel import RuleState, load_rule_rows, save_rule_rows
        from std import LINT_RULES

        with tempfile.TemporaryDirectory(prefix="zfr-lintsel-") as tmp:
            root = Path(tmp)
            (root / ".config" / "zfr").mkdir(parents=True)
            (root / ".config" / "zfr" / "lint.options").write_text("-l 2\n", encoding="utf-8")
            # Minimal tree so file-scoped rules (e.g. ZL0090) match.
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
            (root / "meson.build").write_text("project('t')\n", encoding="utf-8")
            rows = load_rule_rows(root)
            self.assertTrue(rows, "expected matching lint rules")
            rows[0].state = RuleState.IGNORED
            # find an izeable rule to mark always
            for r in rows:
                if r.rule.id == "ZL0090":
                    r.state = RuleState.ALWAYS
                    break
            else:
                self.fail("ZL0090 should match src/app.py")
            path = save_rule_rows(root, rows)
            text = path.read_text(encoding="utf-8")
            self.assertIn("-l 2", text)
            self.assertIn("-u ", text)
            self.assertIn("--always ", text)
            loaded = load_rule_rows(root)
            by_id = {r.rule.id: r.state for r in loaded}
            self.assertEqual(by_id[rows[0].rule.id], RuleState.IGNORED)
            self.assertEqual(by_id["ZL0090"], RuleState.ALWAYS)
            self.assertTrue(any(r.izeable for r in LINT_RULES.all_rules()))


class FilterAlwaysTests(unittest.TestCase):
    def test_always_overrides_uncheck(self) -> None:
        from finding import Finding
        from lint.filtering import filter_findings

        findings = [
            Finding("warn", "source.hardcoded.path", "x"),
            Finding("warn", "rpm.missing", "y"),
        ]
        out = filter_findings(findings, uncheck=["ZL0090", "ZL0026"], always=["ZL0090"])
        codes = {f.code for f in out}
        self.assertIn("source.hardcoded.path", codes)
        self.assertNotIn("rpm.missing", codes)


class IzeableTableTests(unittest.TestCase):
    def test_table_has_fix_column(self) -> None:
        from std import LINT_RULES, render_std_table

        table = render_std_table(LINT_RULES.all_rules())
        self.assertIn("Fix", table)
        self.assertIn("ize", table)
        self.assertIn("ZL0095", table)
        self.assertIn("ZL0096", table)


if __name__ == "__main__":
    unittest.main()
