# SPDX-License-Identifier: AGPL-3.0-or-later
"""Release artifact discovery (version-scoped packaging outs)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zfr_lib.release.artifacts import (
    artifact_name_matches_version,
    find_packaging_out_artifacts,
)


class ArtifactVersionMatchTests(unittest.TestCase):
    def test_mingw_version_not_prefix(self) -> None:
        self.assertTrue(
            artifact_name_matches_version("zephyr_mingw-2.8.16.exe", "2.8.16")
        )
        self.assertFalse(
            artifact_name_matches_version("zephyr_mingw-2.8.1.exe", "2.8.16")
        )
        self.assertTrue(
            artifact_name_matches_version("zephyr_mingw-2.8.1.exe", "2.8.1")
        )

    def test_find_packaging_out_filters_stale(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zfr-out-") as tmp:
            root = Path(tmp)
            out = root / "packaging" / "win32" / "mingw" / "out"
            out.mkdir(parents=True)
            (out / "zephyr_mingw-2.8.1.exe").write_bytes(b"old")
            (out / "zephyr_mingw-2.8.16.exe").write_bytes(b"new")
            (out / "readme.txt").write_text("x", encoding="utf-8")
            found = find_packaging_out_artifacts(
                root, version="2.8.16", pkg="zephyr"
            )
            self.assertEqual(
                [Path(p).name for p in found], ["zephyr_mingw-2.8.16.exe"]
            )


if __name__ == "__main__":
    unittest.main()
