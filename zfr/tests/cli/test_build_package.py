# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for zfr-build / zfr-package detection helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.buildsys import detect_build_system  # noqa: E402
from zfr_lib.pkg import detect_packaging_kinds, package_deb  # noqa: E402
from zfr_lib.pkg_docker import debian_build_inner  # noqa: E402


class BuildsysDetectTests(unittest.TestCase):
    def test_meson(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text("project('x')\n", encoding="utf-8")
            info = detect_build_system(root)
            assert info is not None
            self.assertEqual(info.name, "meson")

    def test_cmake_over_make(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CMakeLists.txt").write_text("project(x)\n", encoding="utf-8")
            (root / "Makefile").write_text("all:\n\ttrue\n", encoding="utf-8")
            info = detect_build_system(root)
            assert info is not None
            self.assertEqual(info.name, "cmake")

    def test_autotools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "configure.ac").write_text("AC_INIT([x],[1])\n", encoding="utf-8")
            info = detect_build_system(root)
            assert info is not None
            self.assertEqual(info.name, "autotools")


class PackagingDetectTests(unittest.TestCase):
    def test_deb_and_rpm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "debian").mkdir()
            (root / "debian" / "control").write_text("Source: x\n", encoding="utf-8")
            (root / "packaging" / "rpm").mkdir(parents=True)
            (root / "packaging" / "rpm" / "Makefile").write_text("all:\n", encoding="utf-8")
            kinds = [k.name for k in detect_packaging_kinds(root)]
            self.assertIn("deb", kinds)
            self.assertIn("rpm", kinds)

    def test_npm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text('{"name":"x"}\n', encoding="utf-8")
            kinds = [k.name for k in detect_packaging_kinds(root)]
            self.assertEqual(kinds, ["npm"])


class DockerDebianExtractTests(unittest.TestCase):
    def test_inner_script_uses_debuild(self) -> None:
        script = debian_build_inner("zephyr", ["-us", "-uc"], jobs=4)
        self.assertIn("cd zephyr", script)
        self.assertIn("debuild", script)
        self.assertIn("-j4", script)
        self.assertIn("parallel=4", script)
        self.assertIn("-us", script)
        self.assertIn("mk-build-deps", script)

    def test_package_deb_docker_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            root.mkdir()
            (root / "debian").mkdir()
            (root / "debian" / "control").write_text("Source: x\n", encoding="utf-8")
            # dry-run must not require build4/docker on PATH
            package_deb(root, docker=True, dry_run=True)


if __name__ == "__main__":
    unittest.main()
