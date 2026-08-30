# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lint-related CLI and source-size tests."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import ROOT, add_src_to_path

add_src_to_path()


class LintStyleInfoDefaultsTests(unittest.TestCase):
    def test_non_interactive_defaults_info_on(self) -> None:
        from zfr_lib.terminal import default_lint_style_info

        with patch.object(sys.stdout, "isatty", return_value=False):
            self.assertTrue(default_lint_style_info())

    def test_plain_interactive_shell_defaults_info_off(self) -> None:
        from zfr_lib.terminal import default_lint_style_info

        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "TERM_PROGRAM",
                "TERM_PROGRAM_VERSION",
                "VSCODE_PID",
                "VSCODE_GIT_IPC_HANDLE",
                "CURSOR_TRACE_ID",
                "CURSOR_AGENT",
            }
        }
        with patch.object(sys.stdout, "isatty", return_value=True):
            with patch.dict(os.environ, env, clear=True):
                self.assertFalse(default_lint_style_info())

    def test_cursor_terminal_defaults_info_on(self) -> None:
        from zfr_lib.terminal import default_lint_style_info

        with patch.object(sys.stdout, "isatty", return_value=True):
            with patch.dict(os.environ, {"TERM_PROGRAM": "cursor"}, clear=False):
                self.assertTrue(default_lint_style_info())

    def test_vscode_pid_defaults_info_on(self) -> None:
        from zfr_lib.terminal import default_lint_style_info

        env = {k: v for k, v in os.environ.items() if k != "TERM_PROGRAM"}
        env["VSCODE_PID"] = "12345"
        with patch.object(sys.stdout, "isatty", return_value=True):
            with patch.dict(os.environ, env, clear=True):
                self.assertTrue(default_lint_style_info())

    def test_windsurf_terminal_defaults_info_on(self) -> None:
        from zfr_lib.terminal import default_lint_style_info

        with patch.object(sys.stdout, "isatty", return_value=True):
            with patch.dict(os.environ, {"TERM_PROGRAM": "windsurf"}, clear=False):
                self.assertTrue(default_lint_style_info())


class ZephyrLintSourceTests(unittest.TestCase):
    def test_skips_example_commons_module(self) -> None:
        from zfr_lib.lint.source_size import check_source_size
        from zfr_lib.lint.util import is_example_shared_src

        with tempfile.TemporaryDirectory(prefix="zfr-lint-src-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            commons = root / "src" / "commons.py"
            commons.write_text("\n".join(f"x = {i}" for i in range(800)), encoding="utf-8")
            self.assertTrue(is_example_shared_src(root, commons))
            findings = check_source_size(root, "app")
            self.assertFalse(any(f.code == "source.long" for f in findings))

    def test_template_coverage_skips_commons_and_renames_spec(self) -> None:
        from zfr_lib.lint.template import check_template_gaps, _expected_rel
        from zfr_lib.lint.util import is_example_shared_rel

        self.assertTrue(is_example_shared_rel(Path("src/commons.c")))
        self.assertTrue(is_example_shared_rel(Path("src/commons.h")))
        self.assertTrue(is_example_shared_rel(Path("tests/commons_test.c")))
        self.assertTrue(is_example_shared_rel(Path("tests/test_commons.py")))
        self.assertFalse(is_example_shared_rel(Path("src/app.c")))
        self.assertEqual(
            _expected_rel(Path("packaging/rpm/zephyr.spec"), "myproj").as_posix(),
            "packaging/rpm/myproj.spec",
        )
        self.assertEqual(
            _expected_rel(Path("debian/zephyr.substvars"), "myproj").as_posix(),
            "debian/myproj.substvars",
        )

        with tempfile.TemporaryDirectory(prefix="zfr-tmpl-cov-") as tmp:
            root = Path(tmp)
            (root / "packaging" / "rpm").mkdir(parents=True)
            (root / "packaging" / "rpm" / "demo.spec").write_text("Name: demo\n", encoding="utf-8")
            (root / "debian").mkdir()
            (root / "debian" / "control").write_text(
                "Source: demo\n\nPackage: demo\nDescription: demo\n",
                encoding="utf-8",
            )
            (root / "debian" / "demo.substvars").write_text("misc:Depends=\n", encoding="utf-8")
            (root / "meson.build").write_text("project('demo')\n", encoding="utf-8")
            findings = check_template_gaps(root, "c", "app")
            msgs = " ".join(f.message for f in findings if f.code == "template.coverage")
            self.assertNotIn("commons", msgs)
            self.assertNotIn("zephyr.spec", msgs)
            self.assertNotIn("zephyr.substvars", msgs)
            self.assertNotIn("substvars", msgs)
            self.assertNotRegex(msgs, r"packaging/rpm/\S+\.spec")

    def test_warns_on_very_long_source(self) -> None:
        from zfr_lib.lint.source_size import check_source_size

        with tempfile.TemporaryDirectory(prefix="zfr-lint-long-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            long = root / "src" / "big.py"
            long.write_text("\n".join(f"x = {i}" for i in range(1100)), encoding="utf-8")
            findings = check_source_size(root, "app")
            warns = [f for f in findings if f.code == "source.long" and f.severity == "warn"]
            self.assertTrue(warns)
            self.assertIn("big.py", warns[0].file or "")

    def test_medium_source_emits_lint_note(self) -> None:
        from zfr_lib.lint.source_size import check_source_size, _extract_subdir_fix

        with tempfile.TemporaryDirectory(prefix="zfr-lint-med-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            med = root / "src" / "mid.py"
            med.write_text("\n".join(f"x = {i}" for i in range(650)), encoding="utf-8")
            findings = check_source_size(root, "app")
            notes = [f for f in findings if f.severity == "note" and f.code == "source.long"]
            self.assertEqual(len(notes), 1)
            self.assertIn("mid.py", notes[0].file or "")
            self.assertIn("src/mid/", notes[0].fix or "")
            self.assertIn("package subdirectory", _extract_subdir_fix("src/mid.py"))

    def test_zfr_package_has_no_source_size_notes(self) -> None:
        from zfr_lib.lint import collect_findings

        _name, _lang, _role, findings = collect_findings(ROOT)
        notes = [f for f in findings if f.severity == "note"]
        self.assertEqual(notes, [], "\n".join(f"{f.file}: {f.message}" for f in notes))


if __name__ == "__main__":
    unittest.main()
