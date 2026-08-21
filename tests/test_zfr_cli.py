# SPDX-License-Identifier: AGPL-3.0-or-later
"""CLI tests for zephyr subcommands using temporary example projects."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
ZEPHYR = TOOLS / "zfr"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    extra = str(TOOLS)
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = extra if not prev else extra + os.pathsep + prev
    env["ZFR_PKGDATADIR"] = str(ROOT)
    env["NO_COLOR"] = "1"
    env["GIT_AUTHOR_NAME"] = "Zephyr Tests"
    env["GIT_AUTHOR_EMAIL"] = "zephyr-tests@example.com"
    env["GIT_COMMITTER_NAME"] = "Zephyr Tests"
    env["GIT_COMMITTER_EMAIL"] = "zephyr-tests@example.com"
    return env


def run_zephyr(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(ZEPHYR), *args],
        cwd=cwd or ROOT,
        env=_env(),
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"zfr {' '.join(args)} failed ({proc.returncode})\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


class ZephyrHelpTests(unittest.TestCase):
    def test_help_lists_subcommands(self) -> None:
        proc = run_zephyr("help")
        for cmd in (
            "create",
            "rename",
            "add",
            "remove",
            "about",
            "version",
            "lint",
            "shape",
            "dist",
            "ize",
            "detect",
        ):
            self.assertIn(cmd, proc.stdout)

    def test_ize_wrapper_help(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(TOOLS / "zfr-ize"), "--help"],
            env=_env(),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("dry-run", proc.stdout)


class ZephyrDetectTests(unittest.TestCase):
    def test_detect_python_template(self) -> None:
        proc = run_zephyr("detect", cwd=ROOT / "python")
        self.assertIn("packagedir:", proc.stderr)
        self.assertIn("repodir:", proc.stderr)

    def test_detect_bash_template(self) -> None:
        proc = run_zephyr("detect", cwd=ROOT / "bash")
        self.assertEqual(proc.stdout.strip(), "bash")

    def test_detect_meta_repo_fails(self) -> None:
        proc = run_zephyr("detect", cwd=ROOT, check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("meta-repo", proc.stderr)

    def test_shape_score_and_bool(self) -> None:
        proc = run_zephyr("shape", cwd=ROOT / "python")
        score = int(proc.stdout.strip())
        self.assertGreaterEqual(score, 50)
        self.assertLessEqual(score, 100)
        b = run_zephyr("shape", "-b", "-v", cwd=ROOT / "python")
        self.assertEqual(b.stdout.strip(), "1")
        self.assertIn("# packagedir=", b.stderr)
        self.assertIn("# repodir=", b.stderr)


class ZephyrCreateProjectTests(unittest.TestCase):
    """create / add / remove / about / version / lint on a bash example project."""

    tmp: tempfile.TemporaryDirectory[str]
    project: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(prefix="zephyr-cli-")
        cls.project = Path(cls.tmp.name) / "cli_demo"
        run_zephyr(
            "create",
            "-l",
            "bash",
            "-1",
            "0.0.1",
            "-D",
            "unstable",
            str(cls.project),
            "hello",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_create_layout(self) -> None:
        self.assertTrue((self.project / "meson.build").is_file())
        self.assertTrue((self.project / "debian" / "control").is_file())
        self.assertTrue((self.project / "debian" / "changelog").is_file())
        self.assertTrue((self.project / "VERSION").is_file())
        self.assertTrue((self.project / ".githooks" / "pre-commit").is_file())
        self.assertTrue((self.project / "src" / "hello.in").is_file())
        self.assertTrue((self.project / "docs" / "hello.adoc").is_file())
        self.assertFalse((self.project / "src" / "some_puff1.in").exists())
        control = (self.project / "debian" / "control").read_text(encoding="utf-8")
        self.assertIn("Source: cli_demo", control)
        meson = (self.project / "meson.build").read_text(encoding="utf-8")
        self.assertIn("project(", meson)
        self.assertIn("cli_demo", meson)

    def test_detect_version_about(self) -> None:
        det = run_zephyr("detect", cwd=self.project)
        self.assertEqual(det.stdout.strip(), "bash")
        ver = run_zephyr("version", cwd=self.project)
        self.assertTrue(ver.stdout.strip())
        rpm = run_zephyr("version", "-r", cwd=self.project)
        self.assertNotIn("-", rpm.stdout.strip())
        about = run_zephyr("about", cwd=self.project)
        self.assertIn("cli_demo", about.stdout)

    def test_lint(self) -> None:
        proc = run_zephyr("lint", cwd=self.project, check=False)
        self.assertIn("zfr lint", proc.stdout)
        self.assertRegex(proc.stdout, r"status:.*(PASS|FAIL)")

    def test_add_and_remove(self) -> None:
        run_zephyr("add", "world", cwd=self.project)
        self.assertTrue((self.project / "src" / "world.in").is_file())
        run_zephyr("remove", "world", cwd=self.project)
        self.assertFalse((self.project / "src" / "world.in").exists())


class ZephyrRenameTests(unittest.TestCase):
    def test_rename_template_copy(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-rename-") as tmp:
            dest = Path(tmp) / "scratch"
            shutil.copytree(
                ROOT / "bash",
                dest,
                ignore=shutil.ignore_patterns(
                    "build", "rpmbuild", ".git", "__pycache__", ".cache"
                ),
            )
            run_zephyr("rename", "widgets", "hello", cwd=dest)
            meson = (dest / "meson.build").read_text(encoding="utf-8")
            self.assertIn("project(", meson)
            self.assertTrue((dest / "src" / "hello.in").is_file())
            self.assertFalse((dest / "src" / "some_puff1.in").exists())
            control = (dest / "debian" / "control").read_text(encoding="utf-8")
            self.assertIn("Source: widgets", control)


class ZephyrDistTests(unittest.TestCase):
    def test_nested_template_packs_only_that_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-dist-") as tmp:
            out = Path(tmp)
            proc = run_zephyr("dist", "-o", str(out), cwd=ROOT / "bash")
            path = Path(proc.stdout.strip())
            self.assertTrue(path.is_file(), proc.stderr)
            self.assertTrue(path.name.endswith(".tar.xz"))
            listing = subprocess.run(
                ["tar", "-tJf", str(path)],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            self.assertIn("meson.build", listing)
            self.assertNotIn("/python/", listing)
            self.assertNotIn("/tools/", listing)


class ZephyrIzeTests(unittest.TestCase):
    def test_dry_run_on_aligned_bash_template(self) -> None:
        proc = run_zephyr("ize", "-n", cwd=ROOT / "bash")
        self.assertIn("zfr ize", proc.stdout)
        self.assertIn("0 added", proc.stdout)
        self.assertIn("dry-run", proc.stdout)

    def test_ize_synthetic_c_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-ize-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "docs").mkdir()
            (root / "debian").mkdir()
            (root / "meson.build").write_text(
                "project('oldpuff', version: '1.2.3')\n",
                encoding="utf-8",
            )
            (root / "debian" / "control").write_text(
                "Source: oldpuff\n"
                "Maintainer: Lenik <zephyr@bodz.net>\n"
                "Homepage: https://example.com/oldpuff\n"
                "Build-Depends: debhelper-compat (= 13)\n"
                "\n"
                "Package: oldpuff\n"
                "Architecture: any\n"
                "Depends: ${misc:Depends}\n"
                "Description: Old C CLI\n"
                " leftover project\n",
                encoding="utf-8",
            )
            (root / "debian" / "changelog").write_text(
                "oldpuff (1.2.3) unstable; urgency=medium\n\n"
                "  * old\n\n"
                " -- Lenik <zephyr@bodz.net>  Thu, 20 Aug 2026 08:00:00 +0800\n",
                encoding="utf-8",
            )
            (root / "src" / "oldpuff.c").write_text(
                '#include <stdio.h>\n#define VERSION "1.2.3"\n'
                "int main(void) { return 0; }\n",
                encoding="utf-8",
            )
            (root / "docs" / "oldpuff.1").write_text(
                ".TH OLDPUFF 1\n.SH NAME\noldpuff \\- demo\n",
                encoding="utf-8",
            )
            proc = run_zephyr("ize", "-l", "c", cwd=root)
            self.assertIn("zfr ize", proc.stdout)
            meson = (root / "meson.build").read_text(encoding="utf-8")
            self.assertIn("zfr version", meson)
            self.assertIn("run_target", meson)
            self.assertTrue((root / "docs" / "oldpuff.adoc").is_file())
            self.assertFalse((root / "docs" / "oldpuff.1").exists())
            self.assertTrue((root / "rpm" / "oldpuff.spec").is_file() or (root / "rpm" / "zephyr.spec").is_file())
            self.assertTrue((root / "VERSION").is_file())
            self.assertIn("PROJECT_VERSION", (root / "src" / "oldpuff.c").read_text(encoding="utf-8"))
            self.assertTrue((root / "debian" / "rules").is_file())
            mode = (root / "debian" / "rules").stat().st_mode
            self.assertTrue(mode & stat.S_IXUSR)


if __name__ == "__main__":
    unittest.main()
