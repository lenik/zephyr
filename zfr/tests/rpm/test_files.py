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
            self.assertIn(
                "%{_prefix}/lib/python3/dist-packages/demopkg/*", files
            )
            self.assertIn("%{_datadir}/demopkg/", files)

    def test_pkgdatadir_subpath_lists_pkgdata_dir(self) -> None:
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
            self.assertIn("%{_datadir}/zephyr/", files)
            self.assertIn("%{_datadir}/doc/zephyr/", files)

    def test_gettext_domain_from_i18n_gettext(self) -> None:
        meson = """\
project('zephyr', 'c')
i18n = import('i18n')
i18n.gettext('zephyr', install: true)
"""
        with tempfile.TemporaryDirectory(prefix="zfr-rpmf-") as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text(meson, encoding="utf-8")
            (root / "po").mkdir()
            (root / "po" / "de.po").write_text("#\n", encoding="utf-8")
            files = meson_rpm_files(root, "zephyr")
            self.assertIn(
                "%{_datadir}/locale/*/LC_MESSAGES/zephyr.mo", files
            )

    def test_wrapper_names_foreach_bindir(self) -> None:
        meson = """\
project('zephyr', 'c')
bindir = prefix / get_option('bindir')
wrapper_names = ['zfr', 'zfr-lint']
foreach name : wrapper_names
    configure_file(
        input: name + '.in',
        output: name,
        configuration: cfg,
        install: true,
        install_dir: bindir,
    )
endforeach
"""
        with tempfile.TemporaryDirectory(prefix="zfr-rpmf-") as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text(meson, encoding="utf-8")
            files = meson_rpm_files(root, "zephyr")
            self.assertIn("%{_bindir}/zfr", files)
            self.assertIn("%{_bindir}/zfr-lint", files)

    def test_foreach_man_puffs_mandir(self) -> None:
        meson = """\
project('twotree', 'c')
mandir = prefix / get_option('mandir')
man_puffs = ['2tree', 'atree']
foreach puff : man_puffs
  custom_target(
    puff + '-man',
    input: 'docs' / (puff + '.adoc'),
    output: puff + '.1',
    command: ['asciidoctor', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: mandir / 'man1',
  )
endforeach
"""
        with tempfile.TemporaryDirectory(prefix="zfr-rpmf-") as tmp:
            root = Path(tmp)
            (root / "meson.build").write_text(meson, encoding="utf-8")
            files = meson_rpm_files(root, "twotree")
            self.assertIn("%{_mandir}/man1/2tree.1*", files)
            self.assertIn("%{_mandir}/man1/atree.1*", files)

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
