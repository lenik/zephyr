# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for hardcoded path/version lint, tarignore, and cursor-rules refresh."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()


class SourceSizeDocSkipTests(unittest.TestCase):
    def test_docs_and_bash_not_flagged(self) -> None:
        from zfr_lib.lint.source_size import check_source_size

        with tempfile.TemporaryDirectory(prefix="zfr-srcsize-") as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            long = "\n".join(f"line {i}" for i in range(1200))
            (root / "docs" / "app.adoc").write_text(long, encoding="utf-8")
            (root / "README.md").write_text(long, encoding="utf-8")
            (root / "app.bash").write_text(long, encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "tiny.py").write_text("x = 1\n", encoding="utf-8")
            findings = check_source_size(root, "app")
            self.assertFalse(
                any(f.code == "source.long" for f in findings),
                [f.message for f in findings],
            )


class HardcodedLintTests(unittest.TestCase):
    def test_flags_script_path_and_version(self) -> None:
        from zfr_lib.lint.hardcoded import check_hardcoded

        with tempfile.TemporaryDirectory(prefix="zfr-hc-") as tmp:
            root = Path(tmp)
            (root / "debian").mkdir()
            (root / "debian" / "changelog").write_text(
                "demo (1.2.3) testing; urgency=medium\n\n  * x\n\n"
                " -- A <a@b.c>  Fri, 11 Sep 2026 00:00:00 +0000\n",
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src" / "tool.sh").write_text(
                "#!/bin/sh\nDATADIR=/usr/share/demo\necho '1.2.3'\n",
                encoding="utf-8",
            )
            findings = check_hardcoded(root, "app")
            codes = {f.code for f in findings if f.severity == "warn"}
            self.assertIn("source.hardcoded.path", codes)
            self.assertIn("source.hardcoded.version", codes)

    def test_skips_already_templated(self) -> None:
        from zfr_lib.lint.hardcoded import check_hardcoded

        with tempfile.TemporaryDirectory(prefix="zfr-hc-ok-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "tool.in").write_text(
                "#!/bin/sh\necho @VERSION@ @DATADIR@\n",
                encoding="utf-8",
            )
            findings = check_hardcoded(root, "app")
            self.assertTrue(any(f.code == "source.hardcoded" and f.severity == "ok" for f in findings))


class TarIgnoreTests(unittest.TestCase):
    def test_gitignore_style_patterns(self) -> None:
        from zfr_lib.tarignore import TarIgnore

        spec = TarIgnore.from_text(
            "# comment\n"
            "*.o\n"
            "/build/\n"
            "tmp/\n"
            "!tmp/keep\n"
            "secret.txt\n"
        )
        self.assertTrue(spec.match("foo.o"))
        self.assertTrue(spec.match("build", is_dir=True))
        self.assertTrue(spec.match("build/x"))
        self.assertTrue(spec.match("tmp/a"))
        self.assertFalse(spec.match("tmp/keep"))
        self.assertTrue(spec.match("secret.txt"))
        self.assertFalse(spec.match("readme.md"))

    def test_dist_honors_tarignore(self) -> None:
        from zfr_lib.dist import _directory_archive
        from zfr_lib.tarignore import TarIgnore
        import tarfile

        with tempfile.TemporaryDirectory(prefix="zfr-dist-ti-") as tmp:
            root = Path(tmp) / "proj"
            root.mkdir()
            (root / "keep.txt").write_text("ok\n", encoding="utf-8")
            (root / "drop.me").write_text("no\n", encoding="utf-8")
            (root / ".tarignore").write_text("drop.me\n", encoding="utf-8")
            dest = Path(tmp) / "out.tar.gz"
            _directory_archive(
                root,
                dest,
                "proj-1.0",
                fmt="gz",
                tarignore=TarIgnore.load(root),
            )
            with tarfile.open(dest, "r:gz") as tf:
                names = set(tf.getnames())
            self.assertTrue(any(n.endswith("keep.txt") for n in names))
            self.assertFalse(any(n.endswith("drop.me") for n in names))


class CursorRulesPreferSourceTests(unittest.TestCase):
    def test_prefers_in_tree_cursor_rules(self) -> None:
        from zfr_lib.cursor_rules import RULE_NAMES, cursor_rule_src

        for name in RULE_NAMES:
            src = cursor_rule_src(name)
            self.assertIsNotNone(src, name)
            assert src is not None
            self.assertTrue(src.is_file(), name)
            # Running from the checkout → zfr/cursor-rules/
            self.assertIn("cursor-rules", src.as_posix())


if __name__ == "__main__":
    unittest.main()
