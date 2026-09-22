# SPDX-License-Identifier: AGPL-3.0-or-later
"""Scanner prune + gitignore tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from support import add_src_to_path

add_src_to_path()


class GlobCanMatchUnderTests(unittest.TestCase):
    def test_dir_scoped(self) -> None:
        from lint.globmatch import glob_can_match_under

        self.assertTrue(glob_can_match_under("/po/", "/po/"))
        self.assertTrue(glob_can_match_under("/src/", "/{src,tests}/**/*.py"))
        self.assertFalse(glob_can_match_under("/packaging/", "/{src,tests}/**/*.py"))
        self.assertTrue(glob_can_match_under("/debian/", "/debian/control"))
        self.assertFalse(glob_can_match_under("/man/", "/debian/control"))


class GitIgnoreScanTests(unittest.TestCase):
    def test_nested_gitignore_prunes(self) -> None:
        from lint.base import RuleSpec
        from lint.scanner import iter_scan_paths
        import types

        with tempfile.TemporaryDirectory(prefix="zfr-scan-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "a.py").write_text("x\n", encoding="utf-8")
            (root / "debian").mkdir()
            (root / "debian" / ".gitignore").write_text("/zephyr\n", encoding="utf-8")
            (root / "debian" / "zephyr").mkdir()
            (root / "debian" / "zephyr" / "usr").mkdir()
            (root / "debian" / "zephyr" / "usr" / "bin").mkdir()
            (root / "debian" / "zephyr" / "usr" / "bin" / "x").write_text("x\n", encoding="utf-8")
            (root / "debian" / "control").write_text("Source: t\n", encoding="utf-8")

            mod = types.ModuleType("fake")
            rule = RuleSpec(
                id="ZL9999",
                code="test",
                module=mod,
                globs=["/src/", "/debian/", "/debian/control"],
            )
            paths = {p.relative_to(root).as_posix() for p in iter_scan_paths(root, [rule])}
            self.assertIn("src", paths)
            self.assertIn("debian", paths)
            self.assertIn("debian/control", paths)
            self.assertNotIn("debian/zephyr", paths)
            self.assertTrue(all(not p.startswith("debian/zephyr/") for p in paths))

    def test_iter_files_honours_gitignore(self) -> None:
        from lib import iter_files

        with tempfile.TemporaryDirectory(prefix="zfr-iter-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "a.py").write_text("x\n", encoding="utf-8")
            (root / "debian").mkdir()
            (root / "debian" / ".gitignore").write_text("/zephyr\n", encoding="utf-8")
            (root / "debian" / "control").write_text("Source: t\n", encoding="utf-8")
            (root / "debian" / "zephyr").mkdir()
            (root / "debian" / "zephyr" / "usr").mkdir()
            (root / "debian" / "zephyr" / "usr" / "x").write_text("x\n", encoding="utf-8")

            rels = {p.relative_to(root).as_posix() for p in iter_files(root)}
            self.assertIn("src/a.py", rels)
            self.assertIn("debian/control", rels)
            self.assertNotIn("debian/zephyr/usr/x", rels)

            all_rels = {
                p.relative_to(root).as_posix()
                for p in iter_files(root, honour_gitignore=False)
            }
            self.assertIn("debian/zephyr/usr/x", all_rels)


if __name__ == "__main__":
    unittest.main()
