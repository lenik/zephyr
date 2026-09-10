# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for FDM text encode/decode and last-package cache."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.fdm import (  # noqa: E402
    encode_run,
    iter_runs,
    last_line_from_fdm,
    which_fdm_tool,
)
from zfr_lib.pkg_last import (  # noqa: E402
    PackageLastRun,
    PackagerRecord,
    load_last_run,
    record_fdm_path,
    save_last_run,
)


class FdmTextTests(unittest.TestCase):
    def test_encode_and_escape(self) -> None:
        self.assertEqual(encode_run(1, "hi\n"), b"\\1;hi\n")
        self.assertEqual(encode_run(2, "a\\b"), b"\\2;a\\\\b")
        self.assertEqual(encode_run(1, ""), b"")
        blob = encode_run(1, "x", ts=1262978234.233124)
        self.assertTrue(blob.startswith(b"\\1,1262978234.233124;"))
        self.assertTrue(blob.endswith(b"x"))

    def test_iter_runs_order_and_concat(self) -> None:
        blob = encode_run(1, "A") + encode_run(2, "B\\C") + encode_run(1, "D")
        runs = iter_runs(blob)
        self.assertEqual(runs, [(1, b"A"), (2, b"B\\C"), (1, b"D")])

    def test_last_line(self) -> None:
        blob = encode_run(1, "hello\n") + encode_run(2, "warn\n") + encode_run(1, "partial")
        self.assertEqual(last_line_from_fdm(blob), "partial")
        blob2 = encode_run(1, "one\n") + encode_run(2, "two\n")
        self.assertEqual(last_line_from_fdm(blob2), "two")

    def test_fddemux_roundtrip(self) -> None:
        tool = which_fdm_tool("fddemux")
        if not tool:
            self.skipTest("fddemux not on PATH")
        blob = encode_run(1, "OUT\n") + encode_run(2, "ERR\n")
        proc = subprocess.run([tool, "-"], input=blob, capture_output=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, b"OUT\n")
        self.assertEqual(proc.stderr, b"ERR\n")


class PackageLastTests(unittest.TestCase):
    def test_save_load_fdm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_path = root / "last-package.json"
            fdm = root / "deb.fdm"
            fdm.write_bytes(encode_run(1, "ok\n"))
            run = PackageLastRun(
                root="/proj",
                started=1.0,
                finished=2.0,
                jobs=4,
                records=[
                    PackagerRecord("deb", True, "packaged", str(fdm), ""),
                    PackagerRecord("rpm", False, "error: exit 2", "", "exit 2"),
                ],
            )
            save_last_run(run, path=json_path)
            loaded = load_last_run(path=json_path)
            assert loaded is not None
            self.assertEqual(loaded.root, "/proj")
            self.assertEqual(len(loaded.records), 2)
            self.assertEqual([r.name for r in loaded.failures()], ["rpm"])
            self.assertEqual(loaded.records[0].fdm, "deb.fdm")
            dest = json_path.parent / "last-package.d" / "deb.fdm"
            self.assertTrue(dest.is_file())
            self.assertEqual(dest.read_bytes(), encode_run(1, "ok\n"))
            rec = loaded.records[0]
            rec.fdm = str(dest)
            self.assertEqual(record_fdm_path(rec), dest)


class PkgLogHelpTests(unittest.TestCase):
    def test_list_help_mentions_fdmpager(self) -> None:
        from zfr_lib.pkg_logview import LIST_HELP_LINES

        blob = "\n".join(LIST_HELP_LINES)
        self.assertIn("fdmpager", blob)
        self.assertIn("fddemux", blob)
        self.assertIn("Tab", blob)


if __name__ == "__main__":
    unittest.main()
