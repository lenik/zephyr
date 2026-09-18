# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for lint.comments IO and ``zfr comments`` filters."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path, run_zephyr

add_src_to_path()


class CommentsIoTests(unittest.TestCase):
    def test_parse_normalize_4digit(self) -> None:
        from zfr_lib.lint.comments import (
            append_comment,
            delete_comments,
            format_comments,
            load_comments_file,
            normalize_rule_key,
            parse_comments,
            render_comments_report,
        )

        self.assertEqual(normalize_rule_key("ZL1"), "ZL0001")
        self.assertEqual(normalize_rule_key("90"), "ZL0090")
        parsed = parse_comments("[ZL1]\nhello\n\n[ZL90]\nworld\n")
        self.assertIn("ZL0001", parsed)
        self.assertIn("ZL0090", parsed)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / ".config" / "zfr" / "lint.comments"
            append_comment(path, "ZL1", "first note")
            append_comment(path, "ZL0001", "second note")
            data = load_comments_file(path)
            self.assertIn("first note", data["ZL0001"])
            self.assertIn("second note", data["ZL0001"])
            text = format_comments(data)
            self.assertIn("[ZL0001]", text)
            report = render_comments_report(root, rule_ids={"ZL0001"})
            self.assertIn("ZL0001", report)
            self.assertIn("AI hint:", report)
            touched = delete_comments(root, include_user=False, rule_ids={"ZL0001"})
            self.assertTrue(touched)
            self.assertFalse(path.is_file())


class CommentsCliTests(unittest.TestCase):
    def test_comments_help(self) -> None:
        cp = run_zephyr("comments", "--help")
        self.assertEqual(cp.returncode, 0)
        self.assertIn("lint.comments", cp.stdout)
        self.assertIn("--project", cp.stdout)
        self.assertIn("--delete", cp.stdout)

    def test_comments_filter_and_delete(self) -> None:
        from zfr_lib.lint.comments import append_comment, project_comments_path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text("project('t')\n", encoding="utf-8")
            append_comment(project_comments_path(root), "ZL0001", "keep-me")
            append_comment(project_comments_path(root), "ZL0090", "drop-me")
            with mock.patch("zfr_lib.comments_cmd.find_project_dir", return_value=root):
                cp = run_zephyr("comments", "-C", str(root), "-p", "ZL90")
            self.assertEqual(cp.returncode, 0)
            self.assertIn("drop-me", cp.stdout)
            self.assertNotIn("keep-me", cp.stdout)
            cp2 = run_zephyr("comments", "-C", str(root), "-p", "-d", "ZL0090")
            self.assertEqual(cp2.returncode, 0)
            left = project_comments_path(root).read_text(encoding="utf-8")
            self.assertIn("ZL0001", left)
            self.assertNotIn("ZL0090", left)


if __name__ == "__main__":
    unittest.main()
