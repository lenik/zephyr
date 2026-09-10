# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for VSIX marketplace CLI ensure (ovsx / vsce)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.release.marketplace import ensure_pnpm_cli  # noqa: E402


class EnsurePnpmCliTests(unittest.TestCase):
    def test_uses_path_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            with patch("zfr_lib.release.marketplace.shutil.which", return_value="/usr/bin/ovsx"):
                self.assertEqual(
                    ensure_pnpm_cli("ovsx", "ovsx", cwd=cwd),
                    ["/usr/bin/ovsx"],
                )

    def test_uses_pnpm_exec_when_local(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)

            def which(name: str):
                return "/usr/bin/pnpm" if name == "pnpm" else None

            with patch("zfr_lib.release.marketplace.shutil.which", side_effect=which):
                with patch(
                    "zfr_lib.release.marketplace._pnpm_exec_has",
                    return_value=True,
                ):
                    self.assertEqual(
                        ensure_pnpm_cli("ovsx", "ovsx", cwd=cwd),
                        ["pnpm", "exec", "ovsx"],
                    )

    def test_installs_global_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            calls: list[list[str]] = []

            def which(name: str):
                if name == "pnpm":
                    return "/usr/bin/pnpm"
                if name == "ovsx" and calls:
                    return "/home/me/.local/share/pnpm/ovsx"
                return None

            def run(argv, **kwargs):
                calls.append(list(argv))
                class R:
                    returncode = 0
                    stdout = ""
                    stderr = ""
                return R()

            with patch("zfr_lib.release.marketplace.shutil.which", side_effect=which):
                with patch(
                    "zfr_lib.release.marketplace._pnpm_exec_has",
                    return_value=False,
                ):
                    with patch(
                        "zfr_lib.release.marketplace.subprocess.run",
                        side_effect=run,
                    ):
                        with patch("zfr_lib.release.marketplace.log1"):
                            cmd = ensure_pnpm_cli("ovsx", "ovsx", cwd=cwd)
            self.assertEqual(calls[0], ["pnpm", "add", "-g", "ovsx"])
            self.assertEqual(cmd, ["/home/me/.local/share/pnpm/ovsx"])


if __name__ == "__main__":
    unittest.main()
