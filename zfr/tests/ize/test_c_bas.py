# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for C-family bas i18n / logger / gettext spacing helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.lang._c_bas import (  # noqa: E402
    ensure_main_bas_i18n,
    ensure_define_logger,
    ensure_meson_localedir,
    ensure_meson_bas_dep,
    fix_gettext_edge_spaces,
    gettext_has_edge_spaces,
    lint_c_bas,
)


_MAIN_PLAIN = """\
#include "config.h"
#include <stdio.h>

int main(int argc, char **argv) {
    printf("hi\\n");
    return 0;
}
"""

_MAIN_OK = """\
#include "config.h"
#include <bas/locale/i18n.h>
#include <bas/log/deflog.h>
#include <bas/proc/env.h>

define_logger();

int main(int argc, char **argv) {
    const char *exe = self_exe();
    init_i18n(LOCALEDIR);
    (void)exe;
    return 0;
}
"""


class CBasHelperTests(unittest.TestCase):
    def test_gettext_edge_spaces(self) -> None:
        self.assertTrue(gettext_has_edge_spaces('"  hello"'))
        self.assertTrue(gettext_has_edge_spaces('"hello "'))
        self.assertFalse(gettext_has_edge_spaces('"hello\\n"'))
        self.assertFalse(gettext_has_edge_spaces('"repeat for more verbose loggings\\n"'))

    def test_fix_gettext_edge_spaces(self) -> None:
        src = 'fputs(_("  -v, --verbose\\n"), out);\n'
        new, n = fix_gettext_edge_spaces(src)
        self.assertEqual(n, 1)
        self.assertIn('_("-v, --verbose\\n")', new)
        self.assertNotIn('_("  -v', new)

    def test_ensure_main_bas_i18n(self) -> None:
        new, notes = ensure_main_bas_i18n(_MAIN_PLAIN)
        self.assertTrue(notes)
        self.assertIn("#include <bas/locale/i18n.h>", new)
        self.assertIn("#include <bas/proc/env.h>", new)
        self.assertIn("self_exe()", new)
        self.assertIn("init_i18n(LOCALEDIR)", new)

    def test_ensure_define_logger_weak(self) -> None:
        new, notes = ensure_define_logger("#include <stdio.h>\n\nint foo(void) { return 0; }\n", weak=True)
        self.assertIn("deflog.h", new)
        self.assertIn("__attribute__((weak))", new)
        self.assertIn("define_logger();", new)
        self.assertTrue(notes)

    def test_ensure_meson_localedir_and_bas(self) -> None:
        meson = """\
prefix = get_option('prefix')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
config_h = configuration_data()
config_h.set_quoted('PROJECT_VERSION', meson.project_version())
configure_file(output: 'config.h', configuration: config_h)
executable(
    'app',
    'src/app.c',
    install: true,
)
"""
        text, notes = ensure_meson_localedir(meson)
        self.assertIn("localedir", text)
        self.assertIn("LOCALEDIR", text)
        text2, notes2 = ensure_meson_bas_dep(text, lang="c")
        self.assertIn("bas_c_dep", text2)
        self.assertIn("dependency('bas-c'", text2)
        self.assertIn("dependencies: [bas_c_dep]", text2)
        self.assertTrue(notes or notes2)

    def test_lint_flags_missing_and_ok(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-cbas-") as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.c").write_text(_MAIN_PLAIN, encoding="utf-8")
            (root / "meson.build").write_text("project('x', 'c')\n", encoding="utf-8")
            findings = lint_c_bas(root, lang="c")
            codes = {f.code for f in findings if f.severity == "warn"}
            self.assertIn("lang.c.bas.main", codes)
            self.assertIn("lang.c.bas.logger", codes)
            self.assertIn("lang.c.bas.localedir", codes)

            (root / "src" / "app.c").write_text(_MAIN_OK, encoding="utf-8")
            (root / "meson.build").write_text(
                "localedir = prefix / get_option('localedir')\n"
                "config_h.set_quoted('LOCALEDIR', localedir)\n",
                encoding="utf-8",
            )
            findings = lint_c_bas(root, lang="c")
            warns = [f for f in findings if f.severity == "warn"]
            self.assertEqual(warns, [], warns)


if __name__ == "__main__":
    unittest.main()
