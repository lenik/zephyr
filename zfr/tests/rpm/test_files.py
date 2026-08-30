# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for Meson-derived RPM %files (meson_rpm_files)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.ize.rpm_files import meson_rpm_files


class MesonRpmFilesPythonTests(unittest.TestCase):
    def test_python_custom_target_bindir_pypkgdir_pkgdatadir(self) -> None:
        meson = """\
project('demopkg', 'c')

bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
pypkgdir = prefix / 'lib' / 'python3' / 'dist-packages' / meson.project_name()
pkgdatadir = datadir / meson.project_name()

custom_target(
    'qkeygen',
    output: 'qkeygen',
    install: true,
    install_dir: bindir,
)

install_data(
    ['src/demopkg/__init__.py'],
    install_dir: pypkgdir,
)

install_data(
    'example.conf',
    install_dir: pkgdatadir,
)
"""
        with tempfile.TemporaryDirectory(prefix="zfr-rpmf-") as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text(meson, encoding="utf-8")
            files = meson_rpm_files(root, "demopkg")
            self.assertIn("%{_bindir}/qkeygen", files)
            self.assertIn("%{_prefix}/lib/python3/dist-packages/%{name}/*", files)
            self.assertIn("%{_datadir}/%{name}/*", files)

    def test_pkgdatadir_subpath_not_top_level_glob(self) -> None:
        meson = """\
project('zephyr', 'c')
datadir = prefix / get_option('datadir')
pkgdatadir = datadir / meson.project_name()
install_data('VERSION', install_dir: pkgdatadir / 'zfr')
"""
        with tempfile.TemporaryDirectory(prefix="zfr-rpmf-") as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text(meson, encoding="utf-8")
            files = meson_rpm_files(root, "zephyr")
            self.assertNotIn("%{_datadir}/%{name}/*", files)

    def test_install_subdir_bindir(self) -> None:
        meson = """\
project('twomeson', 'c')
bindir = prefix / get_option('bindir')
custom_target(
    'twomeson',
    output: 'twomeson',
    install: true,
    install_dir: bindir,
)
install_subdir(
    'src/_twomeson',
    install_dir: bindir,
)
"""
        with tempfile.TemporaryDirectory(prefix="zfr-rpmf-") as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text(meson, encoding="utf-8")
            files = meson_rpm_files(root, "twomeson")
            self.assertIn("%{_bindir}/twomeson", files)
            self.assertIn("%{_bindir}/_twomeson/", files)


if __name__ == "__main__":
    unittest.main()
