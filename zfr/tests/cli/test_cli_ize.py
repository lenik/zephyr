# SPDX-License-Identifier: AGPL-3.0-or-later
"""CLI tests for zfr ize."""

from __future__ import annotations

import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import REPO, run_zephyr, add_src_to_path

add_src_to_path()


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
            self.assertTrue(
                (root / "packaging" / "rpm" / "oldpuff.spec").is_file()
                or (root / "packaging" / "rpm" / "zephyr.spec").is_file()
            )
            self.assertTrue((root / "VERSION").is_file())
            self.assertIn("PROJECT_VERSION", (root / "src" / "oldpuff.c").read_text(encoding="utf-8"))
            self.assertTrue((root / "debian" / "rules").is_file())
            mode = (root / "debian" / "rules").stat().st_mode
            self.assertTrue(mode & stat.S_IXUSR)

    def test_strip_install_man_drops_adoc(self) -> None:
        from zfr_lib.ize.man import strip_install_man_paths

        text = (
            "install_man('docs/foo.adoc')\n"
            "install_man(['docs/a.adoc', 'man/keep.1'])\n"
        )
        out = strip_install_man_paths(text, set())
        self.assertNotIn(".adoc", out)
        self.assertIn("install_man('man/keep.1')", out)

    def test_patch_debian_control_adds_bd_arch_shlib(self) -> None:
        from zfr_lib.ize.debian import patch_debian_control

        text = (
            "Source: demo\n"
            "Maintainer: A <a@b>\n"
            "Build-Depends: debhelper-compat (= 13)\n"
            "\n"
            "Standards-Version: 4.6.0\n"
            "\n"
            "Package: demo\n"
            "Depends: bash\n"
            "Description: demo\n"
            " long\n"
        )
        new, notes = patch_debian_control(text, lang="bash", uses_bash_shlib=True)
        self.assertIn("asciidoctor", new)
        self.assertIn("meson", new)
        self.assertIn("ninja-build", new)
        self.assertIn("Architecture: all", new)
        self.assertIn("bash-shlib", new)
        self.assertIn("\nPackage: demo\n", new)
        # Blank line inside Source (before Standards-Version) must be gone.
        self.assertNotIn("asciidoctor\n\nStandards-Version", new.replace(" ", ""))
        self.assertTrue(any("Build-Depends" in n or "normalize" in n for n in notes))

    def test_stub_man_adoc_has_name_section(self) -> None:
        from zfr_lib.ize.man import stub_man_adoc

        body = stub_man_adoc("coolcmd", "1", summary="do cool things")
        self.assertIn("= coolcmd(1)", body)
        self.assertIn("coolcmd - do cool things", body)
        self.assertIn(":doctype: manpage", body)



if __name__ == "__main__":
    unittest.main()
