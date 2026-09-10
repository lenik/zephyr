# SPDX-License-Identifier: AGPL-3.0-or-later
"""Parse ``.config/zephyr/<packaging>.build-host`` and SSH hop chains.

Config lookup (first existing file wins, then fallback kinds):

* ``<project>/.config/zephyr/<packaging>.build-host``
* ``$HOME/.config/zephyr/<packaging>.build-host``

Stanzas are separated by blank lines. ``#`` starts a comment. Multiple
hosts are an ``ssh -J`` hop list; only the **last** host's ``build_dir``
is used. Unspecified ``build_dir`` means a remote temporary directory
(not preserved). A set ``build_dir`` implies ``preserved: true`` unless
overridden.

Remote sync/build/fetch is implemented here (``remote_build``).
``packaging/lib/host.sh`` only checks local capability.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

_FALLBACK_KINDS: dict[str, tuple[str, ...]] = {
    "mingw": ("mingw", "win32"),
    "innosetup": ("innosetup", "win32"),
    "wix": ("wix", "win32"),
    "win32": ("win32",),
    "macos": ("macos",),
    "freebsd": ("freebsd",),
    "arch": ("arch",),
    "rpm": ("rpm",),
}

_BOOL_TRUE = {"true", "yes", "1", "on"}
_BOOL_FALSE = {"false", "no", "0", "off"}


@dataclass
class BuildHost:
    name: str | None = None
    host: str | None = None
    user: str | None = None
    password: str | None = None
    identity: str | None = None
    build_dir: str | None = None
    preserved: bool | None = None
    # Remote login shell: bash | cmd | powershell (ps). Optional.
    shell: str | None = None

    @property
    def hostname(self) -> str:
        h, _p = split_host_port(self.host or "")
        return h

    @property
    def port(self) -> str | None:
        _h, p = split_host_port(self.host or "")
        return p

    def effective_preserved(self) -> bool:
        if self.preserved is not None:
            return self.preserved
        return bool(self.build_dir)

    def effective_shell(self, kind: str | None = None) -> str:
        """Shell used on the remote build host.

        Inno Setup / WiX default to ``powershell`` (Windows). Others default to ``bash``.
        """
        if self.shell:
            s = self.shell.strip().lower()
            if s in {"ps", "pwsh", "powershell.exe"}:
                return "powershell"
            if s in {"cmd", "cmd.exe"}:
                return "cmd"
            if s in {"bash", "sh"}:
                return "bash"
            return s
        if kind in {"innosetup", "wix"}:
            return "powershell"
        return "bash"



def split_host_port(host: str) -> tuple[str, str | None]:
    """Split ``host[:port]``. IPv6 literals without brackets are not split."""
    host = host.strip()
    if not host:
        return "", None
    if host.startswith("[") and "]" in host:
        bracket, rest = host[1:].split("]", 1)
        if rest.startswith(":") and rest[1:].isdigit():
            return bracket, rest[1:]
        return bracket, None
    if host.count(":") == 1:
        name, port = host.rsplit(":", 1)
        if port.isdigit():
            return name, port
    return host, None


def _parse_bool(raw: str) -> bool:
    v = raw.strip().lower()
    if v in _BOOL_TRUE:
        return True
    if v in _BOOL_FALSE:
        return False
    raise ValueError(f"invalid boolean: {raw!r}")


def parse_build_host_text(text: str) -> list[BuildHost]:
    """Parse a ``.build-host`` file. Skip stanzas that have no ``host``."""
    hosts: list[BuildHost] = []
    cur = BuildHost()
    had_field = False

    def flush() -> None:
        nonlocal cur, had_field
        if had_field and cur.host:
            hosts.append(cur)
        cur = BuildHost()
        had_field = False

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            if had_field:
                flush()
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()
        if not key:
            continue
        had_field = True
        if key == "name":
            cur.name = val or None
        elif key == "host":
            cur.host = val or None
        elif key == "user":
            cur.user = val or None
        elif key == "password":
            cur.password = val or None
        elif key == "identity":
            cur.identity = os.path.expanduser(val) if val else None
        elif key == "build_dir":
            cur.build_dir = val or None
        elif key == "preserved":
            cur.preserved = _parse_bool(val) if val else None
        elif key == "shell":
            cur.shell = val or None
    if had_field:
        flush()
    return hosts


def parse_build_host_file(path: Path) -> list[BuildHost]:
    return parse_build_host_text(path.read_text(encoding="utf-8"))


def packaging_kind_fallbacks(kind: str) -> tuple[str, ...]:
    return _FALLBACK_KINDS.get(kind, (kind,))


def find_build_host_file(root: Path, kind: str, *, home: Path | None = None) -> Path | None:
    """Return the first matching ``.build-host`` file for *kind*."""
    home = home if home is not None else Path.home()
    roots = (root / ".config" / "zephyr", home / ".config" / "zephyr")
    for k in packaging_kind_fallbacks(kind):
        for base in roots:
            cand = base / f"{k}.build-host"
            if cand.is_file():
                return cand
    return None


def load_build_hosts(root: Path, kind: str, *, home: Path | None = None) -> list[BuildHost]:
    path = find_build_host_file(root, kind, home=home)
    if path is None:
        return []
    return parse_build_host_file(path)


def last_build_dir(hosts: list[BuildHost]) -> str | None:
    """Only the last hop's ``build_dir`` is used."""
    if not hosts:
        return None
    return hosts[-1].build_dir


def last_preserved(hosts: list[BuildHost]) -> bool:
    if not hosts:
        return False
    return hosts[-1].effective_preserved()


def ssh_config_text(hosts: list[BuildHost], *, alias_prefix: str = "zephyr-hop") -> str:
    """OpenSSH config: hop ``i`` ProxyJumps hop ``i-1``. Connect to the last alias."""
    lines: list[str] = [
        "# generated by zfr packaging; do not edit",
        "Host *",
        "  StrictHostKeyChecking accept-new",
        "",
    ]
    for i, h in enumerate(hosts):
        alias = f"{alias_prefix}-{i}"
        hostname, port = split_host_port(h.host or "")
        lines.append(f"Host {alias}")
        if hostname:
            lines.append(f"  HostName {hostname}")
        if port:
            lines.append(f"  Port {port}")
        if h.user:
            lines.append(f"  User {h.user}")
        if h.identity:
            lines.append(f"  IdentityFile {h.identity}")
            lines.append("  IdentitiesOnly yes")
        if i > 0:
            lines.append(f"  ProxyJump {alias_prefix}-{i - 1}")
        lines.append("")
    return "\n".join(lines) + "\n"


def last_ssh_alias(hosts: list[BuildHost], *, alias_prefix: str = "zephyr-hop") -> str:
    if not hosts:
        raise ValueError("no build hosts")
    return f"{alias_prefix}-{len(hosts) - 1}"


def jump_spec(host: BuildHost) -> str:
    """``user@hostname:port`` fragment for ``ssh -J``."""
    hostname, port = split_host_port(host.host or "")
    spec = hostname
    if host.user:
        spec = f"{host.user}@{spec}"
    if port:
        spec = f"{spec}:{port}"
    return spec


def ssh_jump_argument(hosts: list[BuildHost]) -> str | None:
    """Comma-separated ``-J`` value for all hops except the last, or None."""
    if len(hosts) < 2:
        return None
    return ",".join(jump_spec(h) for h in hosts[:-1])


def can_build_local(kind: str) -> bool:
    """Whether this machine can run *kind* natively or via a known cross tool."""
    system = sys.platform
    windows = system in {"win32", "cygwin"} or os.environ.get("MSYSTEM", "").startswith("MINGW")
    if kind == "mingw":
        if windows:
            return shutil.which("gcc") is not None or shutil.which("meson") is not None
        return shutil.which("x86_64-w64-mingw32-gcc") is not None or shutil.which(
            "i686-w64-mingw32-gcc"
        ) is not None
    if kind == "innosetup":
        if windows:
            return True
        if shutil.which("iscc") or shutil.which("ISCC"):
            return True
        if shutil.which("wine") is None:
            return False
        for d in innosetup_search_dirs():
            if (d / "ISCC.exe").is_file():
                return True
        return False
    if kind == "wix":
        if windows:
            return True
        return bool(
            shutil.which("wix") or shutil.which("candle") or shutil.which("wixl")
        )
    if kind == "macos":
        return system == "darwin"
    if kind == "freebsd":
        if system.startswith("freebsd"):
            return True
        try:
            return os.uname().sysname == "FreeBSD"
        except AttributeError:
            return False
    if kind == "arch":
        return Path("/etc/arch-release").is_file() and shutil.which("makepkg") is not None
    if kind == "rpm":
        return shutil.which("rpmbuild") is not None
    if kind == "win32":
        return can_build_local("mingw") or can_build_local("innosetup") or can_build_local("wix")
    return False


def innosetup_search_dirs() -> list[Path]:
    home = Path.home()
    env = os.environ.get("INNOSETUP_DIR")
    dirs: list[Path] = []
    if env:
        dirs.append(Path(env))
    dirs.extend(
        [
            home / ".wine/drive_c/Program Files (x86)/Inno Setup 6",
            home / ".wine/drive_c/Program Files/Inno Setup 6",
            home / ".wine/drive_c/Program Files (x86)/Inno Setup 5",
            Path("/opt/inno-setup"),
        ]
    )
    return dirs


_RSYNC_EXCLUDES = (
    ".git",
    ".hg",
    ".svn",
    "build",
    "builddir",
    "rpmbuild",
    "__pycache__",
    ".cache",
    "meson-private",
    "meson-logs",
    "meson-info",
    "dist",
    "node_modules",
    "target",
    "cargo-target",
    ".cursor",
    ".vscode",
    "packaging/win32/mingw/out",
    "packaging/win32/innosetup/out",
    "packaging/win32/wix/out",
    "packaging/macos/out",
    "packaging/freebsd/out",
    "packaging/arch/out",
    "packaging/rpm/out",
    "rpm/out",
)

_OUT_RELS = (
    "packaging/win32/mingw/out",
    "packaging/win32/innosetup/out",
    "packaging/win32/wix/out",
    "packaging/macos/out",
    "packaging/freebsd/out",
    "packaging/arch/out",
    "packaging/rpm/out",
    "rpm/out",
)


def _ssh_base(cfg: Path, hosts: list[BuildHost]) -> list[str]:
    last = hosts[-1]
    cmd = ["ssh", "-F", str(cfg)]
    if last.password and shutil.which("sshpass"):
        return ["env", f"SSHPASS={last.password}", "sshpass", "-e", *cmd]
    return cmd


def _run(
    cmd: list[str],
    *,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    from .fdm import fdmux_capture, get_capture, log_line

    log_line("+ " + " ".join(shlex.quote(c) for c in cmd))
    cap = get_capture()
    if capture:
        proc = subprocess.run(cmd, check=check, text=True, capture_output=True)
        if cap is not None:
            if proc.stdout:
                cap.append_run(
                    1, proc.stdout if proc.stdout.endswith("\n") else proc.stdout + "\n"
                )
            if proc.stderr:
                cap.append_run(
                    2, proc.stderr if proc.stderr.endswith("\n") else proc.stderr + "\n"
                )
        return proc
    if cap is None:
        return subprocess.run(cmd, check=check, text=True)

    rc = fdmux_capture(cmd, cap)
    result = subprocess.CompletedProcess(cmd, rc, "", "")
    if check and rc != 0:
        raise subprocess.CalledProcessError(rc, cmd)
    return result


def _remote_shell_cmd(
    kind: str,
    shell: str,
    remote: str,
    *,
    local_cmd: list[str] | None = None,
) -> str:
    """Command string executed on the remote host."""
    if kind == "innosetup" and shell in {"powershell", "cmd"}:
        if shell == "cmd":
            return (
                f'cmd.exe /c "cd /d {remote}\\packaging\\win32\\innosetup '
                f'&& set ZEPHYR_FORCE_LOCAL=1 && build.cmd"'
            )
        return (
            "powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Set-Location -LiteralPath '{remote}\\packaging\\win32\\innosetup'; "
            "$env:ZEPHYR_FORCE_LOCAL='1'; & .\\build.ps1\""
        )
    if kind == "wix" and shell in {"powershell", "cmd"}:
        if shell == "cmd":
            return (
                f'cmd.exe /c "cd /d {remote}\\packaging\\win32\\wix '
                f'&& set ZEPHYR_FORCE_LOCAL=1 && build.cmd"'
            )
        return (
            "powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Set-Location -LiteralPath '{remote}\\packaging\\win32\\wix'; "
            "$env:ZEPHYR_FORCE_LOCAL='1'; & .\\build.ps1\""
        )
    if local_cmd:
        # Single "!..." entry is a raw shell fragment (e.g. TOPDIR=...).
        if len(local_cmd) == 1 and local_cmd[0].startswith("!"):
            inner = local_cmd[0][1:]
        else:
            inner = " ".join(shlex.quote(c) for c in local_cmd)
    else:
        inner = "true"
    return (
        f"cd {shlex.quote(remote)} && "
        f"export ZEPHYR_FORCE_LOCAL=1 ZEPHYR_SRCDIR={shlex.quote(remote)} && {inner}"
    )


def remote_build(
    root: Path,
    kind: str,
    *,
    local_cmd: list[str],
    out_rels: tuple[str, ...] | None = None,
) -> None:
    """Sync *root* to remote, run build, copy ``out/`` artifacts back, clean if needed."""
    hosts = load_build_hosts(root, kind)
    if not hosts:
        raise FileNotFoundError(f"no .build-host for packaging kind {kind!r}")

    last = hosts[-1]
    shell = last.effective_shell(kind)
    preserved = last.effective_preserved()
    out_rels = out_rels if out_rels is not None else _OUT_RELS

    with tempfile.TemporaryDirectory(prefix="zfr-build-host-") as tmp:
        cfg = Path(tmp) / "ssh_config"
        cfg.write_text(ssh_config_text(hosts), encoding="utf-8")
        ssh = _ssh_base(cfg, hosts)
        alias = last_ssh_alias(hosts)
        rsh = " ".join(shlex.quote(c) for c in ssh)

        if last.build_dir:
            remote = last.build_dir
        elif shell in {"powershell", "cmd"}:
            mk = (
                "powershell.exe -NoLogo -NoProfile -Command "
                f"\"$d = Join-Path $env:TEMP ('zephyr-{kind}.' + "
                "[guid]::NewGuid().ToString('N').Substring(0,8)); "
                "New-Item -ItemType Directory -Path $d | Out-Null; Write-Output $d\""
            )
            proc = _run([*ssh, alias, mk])
            remote = proc.stdout.strip().splitlines()[-1].strip()
        else:
            proc = _run([*ssh, alias, f"mktemp -d /tmp/zephyr-{kind}.XXXXXX"])
            remote = proc.stdout.strip().splitlines()[-1].strip()

        from .fdm import log_line

        log_line(
            f"zfr package: remote {kind} → {alias}:{remote} "
            f"(shell={shell} preserved={preserved})"
        )

        if shell in {"powershell", "cmd"}:
            _run(
                [
                    *ssh,
                    alias,
                    "powershell.exe -NoLogo -NoProfile -Command "
                    f"\"New-Item -ItemType Directory -Force -Path '{remote}' | Out-Null\"",
                ]
            )
        else:
            _run([*ssh, alias, f"mkdir -p {shlex.quote(remote)}"])

        rsync = ["rsync", "-a", "--delete"]
        for ex in _RSYNC_EXCLUDES:
            rsync.append(f"--exclude={ex}")
        rsync.extend(["-e", rsh, f"{root}/", f"{alias}:{remote}/"])
        _run(rsync)

        remote_cmd = _remote_shell_cmd(kind, shell, remote, local_cmd=local_cmd)
        proc = _run([*ssh, alias, remote_cmd], check=False, capture=False)
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, remote_cmd)

        for rel in out_rels:
            remote_out = f"{remote}/{rel}".replace("\\", "/")
            if shell in {"powershell", "cmd"}:
                test = _run(
                    [
                        *ssh,
                        alias,
                        "powershell.exe -NoLogo -NoProfile -Command "
                        f"\"if (Test-Path -LiteralPath '{remote_out}' -PathType Container) "
                        "{ exit 0 } else { exit 1 }\"",
                    ],
                    check=False,
                )
            else:
                test = _run(
                    [*ssh, alias, f"test -d {shlex.quote(remote_out)}"],
                    check=False,
                )
            if test.returncode != 0:
                continue
            dest = root / rel
            dest.mkdir(parents=True, exist_ok=True)
            _run(["rsync", "-a", "-e", rsh, f"{alias}:{remote_out}/", f"{dest}/"])

        if not preserved:
            if shell in {"powershell", "cmd"}:
                _run(
                    [
                        *ssh,
                        alias,
                        "powershell.exe -NoLogo -NoProfile -Command "
                        f"\"Remove-Item -Recurse -Force -LiteralPath '{remote}' "
                        "-ErrorAction SilentlyContinue\"",
                    ],
                    check=False,
                )
            else:
                _run([*ssh, alias, f"rm -rf {shlex.quote(remote)}"], check=False)
