# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for marked stream encode/decode and last-package cache."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.pkg_last import (  # noqa: E402
    PackageLastRun,
    PackagerRecord,
    load_last_run,
    save_last_run,
)
from zfr_lib.stream_mark import (  # noqa: E402
    decode_marked,
    encode_marked,
    replay_marked,
)


class StreamMarkTests(unittest.TestCase):
    def test_roundtrip_order_and_escape(self) -> None:
        chunks = [
            ("out", "hello\n"),
            ("err", "warn </out> leak\n"),
            ("out", "done\n"),
        ]
        marked = encode_marked(chunks)  # type: ignore[arg-type]
        self.assertIn("<out>", marked)
        self.assertIn("<err>", marked)
        self.assertIn("&lt;/out&gt;", marked)
        decoded = decode_marked(marked)
        self.assertEqual(decoded, chunks)

    def test_replay_splits_streams(self) -> None:
        marked = encode_marked(
            [
                ("out", "A"),
                ("err", "B"),
                ("out", "C"),
            ]
        )
        out = io.StringIO()
        err = io.StringIO()
        replay_marked(marked, out=out, err=err)
        self.assertEqual(out.getvalue(), "AC")
        self.assertEqual(err.getvalue(), "B")


class PackageLastTests(unittest.TestCase):
    def test_save_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "last.json"
            run = PackageLastRun(
                root="/proj",
                started=1.0,
                finished=2.0,
                jobs=4,
                records=[
                    PackagerRecord("deb", True, "packaged", "<out>ok</out>", ""),
                    PackagerRecord("rpm", False, "error: exit 2", "<err>boom</err>", "exit 2"),
                ],
            )
            save_last_run(run, path=path)
            loaded = load_last_run(path=path)
            assert loaded is not None
            self.assertEqual(loaded.root, "/proj")
            self.assertEqual(len(loaded.records), 2)
            self.assertEqual([r.name for r in loaded.failures()], ["rpm"])


if __name__ == "__main__":
    unittest.main()
