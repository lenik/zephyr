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
REPO = ROOT.parent
TOOLS = ROOT / "src"
ZEPHYR = TOOLS / "zfr"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    extra = str(TOOLS)
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = extra if not prev else extra + os.pathsep + prev
    env["ZFR_PKGDATADIR"] = str(REPO)
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
            "release",
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
        proc = run_zephyr("detect", cwd=REPO / "python")
        self.assertIn("packagedir:", proc.stderr)
        self.assertIn("repodir:", proc.stderr)

    def test_detect_bash_template(self) -> None:
        proc = run_zephyr("detect", cwd=REPO / "bash")
        self.assertEqual(proc.stdout.strip(), "bash")

    def test_detect_new_language_templates(self) -> None:
        for lang in (
            "lua",
            "zig",
            "kotlin",
            "elixir",
            "nim",
            "ocaml",
            "antlr",
            "bison",
            "as",
            "gcc",
            "pascal",
            "fortran",
            "cobol",
            "d",
        ):
            with self.subTest(lang=lang):
                d = REPO / lang
                if not (d / "meson.build").is_file():
                    self.skipTest(f"missing {lang}/meson.build")
                proc = run_zephyr("detect", cwd=d)
                self.assertEqual(proc.stdout.strip(), lang)

    def test_create_new_language_templates(self) -> None:
        for lang in (
            "lua",
            "zig",
            "kotlin",
            "elixir",
            "nim",
            "ocaml",
            "antlr",
            "bison",
            "as",
            "gcc",
            "pascal",
            "fortran",
            "cobol",
            "d",
        ):
            with self.subTest(lang=lang):
                with tempfile.TemporaryDirectory(prefix=f"zfr-{lang}-") as tmp:
                    dest = Path(tmp) / f"{lang}_demo"
                    run_zephyr("create", "-l", lang, "-1", "0.0.1", str(dest), "hello")
                    self.assertTrue((dest / "meson.build").is_file())
                    det = run_zephyr("detect", cwd=dest)
                    self.assertEqual(det.stdout.strip(), lang)

    def test_parser_templates_expose_cli_flags(self) -> None:
        for lang, path in (
            ("bison", REPO / "bison" / "src" / "some_puff1_main.c"),
            ("antlr", REPO / "antlr" / "src" / "Main.java"),
        ):
            with self.subTest(lang=lang):
                text = path.read_text(encoding="utf-8")
                self.assertIn("--dump", text)
                self.assertIn("--format", text)
                self.assertIn("--indent-size", text)
                self.assertIn("--color", text)

    def test_detect_meta_repo_fails(self) -> None:
        proc = run_zephyr("detect", cwd=REPO, check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("meta-repo", proc.stderr)

    def test_shape_score_and_bool(self) -> None:
        proc = run_zephyr("shape", cwd=REPO / "python")
        score = int(proc.stdout.strip())
        self.assertGreaterEqual(score, 50)
        self.assertLessEqual(score, 100)
        b = run_zephyr("shape", "-b", "-v", cwd=REPO / "python")
        self.assertEqual(b.stdout.strip(), "1")
        self.assertIn("# packagedir=", b.stderr)
        self.assertIn("# repodir=", b.stderr)

    def test_lint_uses_git_root_hooks(self) -> None:
        proc = run_zephyr("lint", cwd=ROOT, check=False)
        self.assertIn("zfr lint", proc.stdout)
        self.assertNotIn("no .githooks/pre-commit", proc.stdout)
        verbose = run_zephyr("lint", "-v", cwd=ROOT, check=False)
        self.assertIn("layout.pre-commit", verbose.stdout)
        self.assertIn("syncs VERSION from debian/changelog", verbose.stdout)

    def test_lint_from_meta_root_lints_zfr_cli(self) -> None:
        proc = run_zephyr("lint", cwd=REPO, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("lang=python", proc.stdout)
        self.assertIn("role=package", proc.stdout)
        self.assertRegex(proc.stdout, r"errors=0\s+warnings=0")

    def test_lint_zfr_cli_is_clean(self) -> None:
        proc = run_zephyr("lint", cwd=ROOT, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("lang=python", proc.stdout)
        self.assertIn("role=package", proc.stdout)
        self.assertRegex(proc.stdout, r"errors=0\s+warnings=0")

    def test_detect_zfr_cli_python(self) -> None:
        proc = run_zephyr("detect", cwd=ROOT)
        self.assertEqual(proc.stdout.strip(), "python")
        self.assertIn("role: package", proc.stderr)

    def test_release_wrapper_help(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(TOOLS / "zfr-release"), "--help"],
            env=_env(),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("gh-makerelease", proc.stdout)
        self.assertIn("--local", proc.stdout)
        self.assertIn("--unsigned", proc.stdout)

    def test_release_recomposes_options(self) -> None:
        import argparse

        from zfr_lib.release import add_release_arguments, compose_makerelease_argv

        p = argparse.ArgumentParser()
        add_release_arguments(p)
        ns = p.parse_args(
            ["-l", "--unsigned", "-I", "-vv", "-p", "mentors", "-B", "b4f-debian:sid"]
        )
        argv = compose_makerelease_argv(ns)
        self.assertEqual(
            argv,
            [
                "--unsigned",
                "--dput-host",
                "mentors",
                "--base-image",
                "b4f-debian:sid",
                "--local",
                "--no-install",
                "--verbose",
                "--verbose",
            ],
        )


class ZephyrCreateProjectTests(unittest.TestCase):
    """create / add / remove / about / version / lint on a bash example project."""

    def test_packaging_under_zfr_only(self) -> None:
        self.assertTrue((ROOT / "debian" / "control").is_file())
        self.assertFalse((REPO / "debian" / "control").exists())
        self.assertTrue((REPO / ".githooks" / "pre-commit").is_file())
        self.assertFalse((ROOT / ".githooks" / "pre-commit").exists())
        self.assertTrue((ROOT / "githooks" / "pre-commit").exists())
        self.assertTrue((REPO / "README.md").is_file())
        self.assertTrue((REPO / "README-zh.md").is_file())
        self.assertFalse((ROOT / "README.md").exists())
        self.assertFalse((ROOT / "README-zh.md").exists())

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

    def test_create_uses_git_config_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-gitid-") as tmp:
            tmp_path = Path(tmp)
            cfg = tmp_path / "gitconfig"
            cfg.write_text(
                "[user]\n\tname = Test Author\n\temail = test@example.com\n",
                encoding="utf-8",
            )
            dest = tmp_path / "gitid_demo"
            env = _env()
            env["GIT_CONFIG_GLOBAL"] = str(cfg)
            env["GIT_CONFIG_SYSTEM"] = "/dev/null"
            for key in (
                "GIT_AUTHOR_NAME",
                "GIT_AUTHOR_EMAIL",
                "GIT_COMMITTER_NAME",
                "GIT_COMMITTER_EMAIL",
            ):
                env.pop(key, None)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ZEPHYR),
                    "create",
                    "-l",
                    "bash",
                    "-1",
                    "0.0.1",
                    str(dest),
                    "hello",
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            changelog = (dest / "debian" / "changelog").read_text(encoding="utf-8")
            self.assertIn("Test Author <test@example.com>", changelog)
            log = subprocess.run(
                ["git", "-C", str(dest), "log", "-1", "--format=%an <%ae>"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(log.stdout.strip(), "Test Author <test@example.com>")

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
                REPO / "bash",
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
            proc = run_zephyr("dist", "-o", str(out), cwd=REPO / "bash")
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
            self.assertIn("src/some_puff1.in", listing)
            self.assertNotIn("/python/", listing)
            self.assertNotIn("/zfr/", listing)
            self.assertNotIn("/tools/", listing)


class ZephyrIzeTests(unittest.TestCase):
    def test_dry_run_on_aligned_bash_template(self) -> None:
        proc = run_zephyr("ize", "-n", cwd=REPO / "bash")
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


class ZephyrLangAndI18nTests(unittest.TestCase):
    def test_detect_ignores_control_description(self) -> None:
        """Debian Description must not vote; Depends + sources decide."""
        with tempfile.TemporaryDirectory(prefix="zfr-lang-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "debian").mkdir()
            (root / "debian" / "control").write_text(
                "Source: demo\n"
                "Build-Depends: debhelper-compat (= 13), python3\n"
                "\n"
                "Package: demo\n"
                "Architecture: all\n"
                "Depends: ${python3:Depends}\n"
                "Description: demo that mentions typescript in prose\n"
                " Long description about typescript and nodejs packaging.\n",
                encoding="utf-8",
            )
            proc = run_zephyr("detect", cwd=root)
            self.assertEqual(proc.stdout.strip(), "python")

    def test_help_zh_cn(self) -> None:
        env = _env()
        env["LANGUAGE"] = "zh_CN"
        env["LANG"] = "C.UTF-8"
        env["LC_ALL"] = "C.UTF-8"
        proc = subprocess.run(
            [sys.executable, str(ZEPHYR), "-h"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("模板助手", proc.stdout)


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

    def test_notes_on_medium_source(self) -> None:
        from zfr_lib.lint.source_size import check_source_size

        with tempfile.TemporaryDirectory(prefix="zfr-lint-med-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            med = root / "src" / "mid.py"
            med.write_text("\n".join(f"x = {i}" for i in range(650)), encoding="utf-8")
            findings = check_source_size(root, "app")
            notes = [f for f in findings if f.code == "source.long" and f.severity == "note"]
            self.assertTrue(notes)


if __name__ == "__main__":
    unittest.main()
