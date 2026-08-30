# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for .build-host parsing and hop chains."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.packaging_host import (  # noqa: E402
    find_build_host_file,
    last_build_dir,
    last_preserved,
    last_ssh_alias,
    parse_build_host_text,
    ssh_config_text,
    ssh_jump_argument,
    split_host_port,
)

SAMPLE = """\
# jump host
name: bastion
host: jump.example.com:22
user: ops
identity: ~/.ssh/id_ed25519

name: winbuild
host: 10.0.0.8
user: builder
password: secret
build_dir: /home/builder/src/zephyr
"""


class BuildHostParseTests(unittest.TestCase):
    def test_split_host_port(self) -> None:
        self.assertEqual(split_host_port("example.com:2222"), ("example.com", "2222"))
        self.assertEqual(split_host_port("example.com"), ("example.com", None))
        self.assertEqual(split_host_port("[::1]:22"), ("::1", "22"))

    def test_parse_hops_last_build_dir_only(self) -> None:
        hosts = parse_build_host_text(SAMPLE)
        self.assertEqual(len(hosts), 2)
        self.assertEqual(hosts[0].name, "bastion")
        self.assertIsNone(hosts[0].build_dir)
        self.assertEqual(last_build_dir(hosts), "/home/builder/src/zephyr")
        self.assertTrue(last_preserved(hosts))
        self.assertFalse(hosts[0].effective_preserved())
        self.assertEqual(ssh_jump_argument(hosts), "ops@jump.example.com:22")
        self.assertEqual(last_ssh_alias(hosts), "zephyr-hop-1")

    def test_shell_defaults_for_win_installers(self) -> None:
        hosts = parse_build_host_text("host: win.example.com\n")
        self.assertEqual(hosts[0].effective_shell("innosetup"), "powershell")
        self.assertEqual(hosts[0].effective_shell("wix"), "powershell")
        self.assertEqual(hosts[0].effective_shell("mingw"), "bash")
        hosts = parse_build_host_text("host: win.example.com\nshell: cmd\n")
        self.assertEqual(hosts[0].effective_shell("innosetup"), "cmd")
        hosts = parse_build_host_text("host: win.example.com\nshell: ps\n")
        self.assertEqual(hosts[0].effective_shell("wix"), "powershell")

        hosts = parse_build_host_text("host: win.example.com\n")
        self.assertEqual(last_build_dir(hosts), None)
        self.assertFalse(last_preserved(hosts))

    def test_preserved_override(self) -> None:
        hosts = parse_build_host_text(
            "host: win.example.com\nbuild_dir: /tmp/keep\npreserved: false\n"
        )
        self.assertFalse(last_preserved(hosts))

    def test_ssh_config_proxyjump(self) -> None:
        hosts = parse_build_host_text(SAMPLE)
        cfg = ssh_config_text(hosts)
        self.assertIn("Host zephyr-hop-0", cfg)
        self.assertIn("Host zephyr-hop-1", cfg)
        self.assertIn("ProxyJump zephyr-hop-0", cfg)
        self.assertIn("HostName 10.0.0.8", cfg)

    def test_find_project_then_home_and_win32_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            home = Path(tmp) / "home"
            (home / ".config" / "zephyr").mkdir(parents=True)
            (home / ".config" / "zephyr" / "win32.build-host").write_text(
                "host: from-home\n", encoding="utf-8"
            )
            (root / ".config" / "zephyr").mkdir(parents=True)
            found = find_build_host_file(root, "mingw", home=home)
            self.assertEqual(found.name, "win32.build-host")
            (root / ".config" / "zephyr" / "mingw.build-host").write_text(
                "host: from-project\n", encoding="utf-8"
            )
            found = find_build_host_file(root, "mingw", home=home)
            self.assertEqual(found.name, "mingw.build-host")
            text = found.read_text(encoding="utf-8")
            self.assertIn("from-project", text)


class HostShDumpTests(unittest.TestCase):
    def test_host_sh_dump(self) -> None:
        import subprocess

        script = (
            Path(__file__).resolve().parents[2].parent / "bash" / "packaging" / "lib" / "host.sh"
        )
        if not script.is_file():
            self.skipTest("bash packaging/lib/host.sh missing")
        with tempfile.NamedTemporaryFile("w", suffix=".build-host", delete=False) as fh:
            fh.write(SAMPLE)
            path = fh.name
        try:
            proc = subprocess.run(
                ["bash", str(script), "dump", path],
                check=False,
                capture_output=True,
                text=True,
            )
        finally:
            Path(path).unlink(missing_ok=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("count=2", proc.stdout)
        self.assertIn("last_build_dir=/home/builder/src/zephyr", proc.stdout)
        self.assertIn("last_preserved=true", proc.stdout)
        self.assertIn("password_set=yes", proc.stdout)


if __name__ == "__main__":
    unittest.main()
