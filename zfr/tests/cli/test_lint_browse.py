# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for lint browse helpers (fdm HTML, ize map)."""

from __future__ import annotations

import unittest

from support import add_src_to_path

add_src_to_path()


class FdmHtmlTests(unittest.TestCase):
    def test_ordered_channels(self) -> None:
        from zfr_lib.fdm import encode_run
        from zfr_lib.lint.fdm_html import fdm_to_html

        data = encode_run(1, "out1\n") + encode_run(2, "err1\n") + encode_run(1, "out2\n")
        html = fdm_to_html(data)
        self.assertIn("fdm-out", html)
        self.assertIn("fdm-err", html)
        self.assertIn("out1", html)
        self.assertIn("err1", html)
        # order preserved
        self.assertLess(html.index("out1"), html.index("err1"))
        self.assertLess(html.index("err1"), html.index("out2"))


class IzeMapTests(unittest.TestCase):
    def test_rpm_maps(self) -> None:
        from zfr_lib.lint.ize_map import ize_command_for_lint, ize_targets_for_lint

        self.assertIn("ize.rpm", ize_targets_for_lint("rpm.missing"))
        cmd = ize_command_for_lint("rpm.missing")
        self.assertIsNotNone(cmd)
        assert cmd is not None
        self.assertIn("--only", cmd)
        self.assertIsNone(ize_command_for_lint("source.long"))

    def test_posync_maps(self) -> None:
        from zfr_lib.lint.ize_map import ize_targets_for_lint

        self.assertEqual(ize_targets_for_lint("layout.posync"), ["ize.posync"])


class IzeOnlyTests(unittest.TestCase):
    def test_is_selected(self) -> None:
        from zfr_lib.std import is_selected

        self.assertTrue(is_selected(rule_id="ZI0013", code="ize.rpm", only=set()))
        self.assertTrue(
            is_selected(rule_id="ZI0013", code="ize.rpm", only={"ize.rpm"})
        )
        self.assertFalse(
            is_selected(rule_id="ZI0013", code="ize.rpm", only={"ize.subst"})
        )


class BrowseUiTests(unittest.TestCase):
    def test_shell_has_solve_show_statusbar(self) -> None:
        from zfr_lib.lint.browse import _shell_html, _ui

        html = _shell_html()
        self.assertIn("a.solve", html)
        self.assertIn("UI.solve", html)
        self.assertIn("add-cmt", html)
        self.assertIn("expand-btn", html)
        self.assertIn("sb-bar", html)
        self.assertIn("findings", html)
        self.assertIn("setUiLang", html)
        self.assertIn("patchRuleState", html)
        self.assertIn("data-theme", html)
        self.assertIn("/api/data", html)
        self.assertIn("/api/comment", html)
        self.assertIn("/api/rule-state", html)
        self.assertNotIn("zfr ize --only", html)
        self.assertNotIn("<h1", html)
        ui = _ui("zh_CN")
        self.assertEqual(ui["docs"], "文档")
        self.assertEqual(ui["add_comment"], "添加留言")
        self.assertEqual(ui["solve"], "修复")
        self.assertEqual(ui["project_only"], "仅本项目")
        en = _ui("en")
        self.assertEqual(en["add_comment"], "Add Comment")

    def test_docs_cover_rules(self) -> None:
        from zfr_lib.lint.docs import rule_doc_dict
        from zfr_lib.std import LINT_RULES

        for rule in LINT_RULES.all_rules()[:20]:
            doc = rule_doc_dict(rule.id, rule.code)
            sections = doc["sections"]
            self.assertTrue(sections)
            self.assertTrue(sections[0]["title"])
            self.assertTrue(sections[0]["body"])


if __name__ == "__main__":
    unittest.main()
