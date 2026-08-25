# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for zfr ize --commit version bump / changelog sync."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from zfr_lib.ize.engine import Ize
from zfr_lib.ize.util import (
    bump_patch_version,
    changelog_author,
    resolve_changelog_author,
)


class BumpPatchTests(unittest.TestCase):
    def test_semver_patch(self) -> None:
        self.assertEqual(bump_patch_version("1.2.3"), "1.2.4")
        self.assertEqual(bump_patch_version("1.2"), "1.2.1")
        self.assertEqual(bump_patch_version("0.0.0"), "0.0.1")

    def test_epoch_and_revision(self) -> None:
        self.assertEqual(bump_patch_version("1:2.3.4-5"), "1:2.3.5-5")
        self.assertEqual(bump_patch_version("v1.0.0"), "1.0.1")


class ChangelogAuthorTests(unittest.TestCase):
    def test_reuses_previous_trailer_not_maintainer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-auth-") as tmp:
            root = Path(tmp)
            (root / "debian").mkdir()
            (root / "debian" / "control").write_text(
                "Source: demopkg\nMaintainer: Other Maint <other@ex.com>\n\n"
                "Package: demopkg\nArchitecture: all\nDescription: d\n demo\n",
                encoding="utf-8",
            )
            (root / "debian" / "changelog").write_text(
                "demopkg (1.0.0) testing; urgency=medium\n\n"
                "  * Initial release\n\n"
                " -- Prev Author (张三) <prev@ex.com>  Tue, 25 Aug 2026 00:00:00 +0000\n",
                encoding="utf-8",
            )
            self.assertEqual(
                changelog_author(root),
                ("Prev Author (张三)", "prev@ex.com"),
            )
            self.assertEqual(
                resolve_changelog_author(root),
                ("Prev Author (张三)", "prev@ex.com"),
            )
            self.assertEqual(
                resolve_changelog_author(root, author_override="New <n@n>"),
                ("New", "n@n"),
            )
            self.assertEqual(
                resolve_changelog_author(root, author_override="OnlyName"),
                ("OnlyName", "prev@ex.com"),
            )


class IzeCommitBumpTests(unittest.TestCase):
    def test_bump_for_commit_updates_changelog_and_version(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-ize-c-") as tmp:
            root = Path(tmp)
            (root / "debian").mkdir()
            (root / "debian" / "control").write_text(
                "Source: demopkg\nMaintainer: Other Maint <other@ex.com>\n\n"
                "Package: demopkg\nArchitecture: all\nDescription: d\n demo\n",
                encoding="utf-8",
            )
            (root / "debian" / "changelog").write_text(
                "demopkg (1.0.0) testing; urgency=medium\n\n"
                "  * Initial release\n\n"
                " -- Prev Author <prev@ex.com>  Tue, 25 Aug 2026 00:00:00 +0000\n",
                encoding="utf-8",
            )
            (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
            (root / "meson.build").write_text(
                "project('demopkg', 'c', version: '0.0.0')\n", encoding="utf-8"
            )
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "t@t"], cwd=root, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "t"], cwd=root, check=True, capture_output=True
            )
            subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True
            )

            ize = Ize(
                root,
                lang="bash",
                do_commit=True,
                do_mesonize=False,
                do_man=False,
                do_subst=False,
            )
            ize.note("update", "meson.build", "align project()")
            ver = ize.bump_for_commit()
            self.assertEqual(ver, "1.0.1")
            self.assertEqual((root / "VERSION").read_text(encoding="utf-8").strip(), "1.0.1")
            head = (root / "debian" / "changelog").read_text(encoding="utf-8")
            self.assertTrue(head.startswith("demopkg (1.0.1) testing;"))
            self.assertIn("zfr ize", head)
            # Must reuse previous trailer, not debian/control Maintainer.
            self.assertIn(" -- Prev Author <prev@ex.com>  ", head.split("demopkg (1.0.0)")[0])
            self.assertNotIn("Other Maint", head.split("demopkg (1.0.0)")[0])
            self.assertIn("1.0.1", ize.commit_message())

    def test_author_override(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-ize-a-") as tmp:
            root = Path(tmp)
            (root / "debian").mkdir()
            (root / "debian" / "control").write_text(
                "Source: demopkg\nMaintainer: Other Maint <other@ex.com>\n\n"
                "Package: demopkg\nArchitecture: all\nDescription: d\n demo\n",
                encoding="utf-8",
            )
            (root / "debian" / "changelog").write_text(
                "demopkg (1.0.0) testing; urgency=medium\n\n"
                "  * Initial release\n\n"
                " -- Prev Author <prev@ex.com>  Tue, 25 Aug 2026 00:00:00 +0000\n",
                encoding="utf-8",
            )
            (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
            ize = Ize(
                root,
                lang="bash",
                do_commit=True,
                author="Override <o@o>",
                do_mesonize=False,
                do_man=False,
                do_subst=False,
            )
            ize.note("add", "rpm/Makefile", "from template")
            ize.bump_for_commit()
            head = (root / "debian" / "changelog").read_text(encoding="utf-8")
            self.assertIn(" -- Override <o@o>  ", head.split("demopkg (1.0.0)")[0])


if __name__ == "__main__":
    unittest.main()
