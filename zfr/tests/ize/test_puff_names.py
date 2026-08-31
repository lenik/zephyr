# SPDX-License-Identifier: AGPL-3.0-or-later
"""Command puff discovery for completions / RPM fallbacks."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()


class PuffNamesTests(unittest.TestCase):
    def test_ignores_library_soname_docs_and_src_modules(self) -> None:
        from zfr_lib.ize.util import _puff_names

        with tempfile.TemporaryDirectory(prefix="zfr-puffs-") as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "audiocfg.adoc").write_text(
                "= audiocfg(1)\n\n== NAME\naudiocfg\n",
                encoding="utf-8",
            )
            (docs / "libaudiocfg.so.adoc").write_text(
                "= libaudiocfg.so(3)\n\n== NAME\nlib\n",
                encoding="utf-8",
            )
            (docs / "libaudiocfg.so.1.0.adoc").write_text(
                "= libaudiocfg.so.1.0(3)\n\n== NAME\nlib\n",
                encoding="utf-8",
            )
            src = root / "src"
            src.mkdir()
            for name in ("audiocfg.c", "catalog.c", "parse.c", "session.c", "c_pch.h"):
                (src / name).write_text("/* x */\n", encoding="utf-8")
            (root / "audiocfg.bash").write_text("complete -F _x audiocfg\n", encoding="utf-8")
            (root / "meson.build").write_text(
                "project('audiocfg', 'c')\nexecutable('audiocfg', 'src/audiocfg.c')\n",
                encoding="utf-8",
            )
            self.assertEqual(_puff_names(root), ["audiocfg"])

    def test_ensure_completion_does_not_invent_module_stubs(self) -> None:
        from zfr_lib.ize.engine import Ize

        with tempfile.TemporaryDirectory(prefix="zfr-comp-") as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "tool.adoc").write_text("= tool(1)\n\n== NAME\ntool\n", encoding="utf-8")
            (docs / "libtool.so.adoc").write_text("= libtool.so(3)\n\n", encoding="utf-8")
            src = root / "src"
            src.mkdir()
            (src / "tool.c").write_text("int main(){}\n", encoding="utf-8")
            (src / "helper.c").write_text("void h(){}\n", encoding="utf-8")
            (root / "tool.bash").write_text("complete -F _longopt tool\n", encoding="utf-8")
            (root / "meson.build").write_text(
                "project('tool', 'c')\nexecutable('tool', 'src/tool.c')\n",
                encoding="utf-8",
            )
            ize = Ize(root, lang="c", dry_run=False, verbose=False)
            ize.ensure_completion()
            comp = root / "completions"
            self.assertFalse(comp.exists())
            self.assertFalse(any(root.glob("helper.bash")))
            self.assertFalse(any(root.rglob("libtool*.bash")))


if __name__ == "__main__":
    unittest.main()
