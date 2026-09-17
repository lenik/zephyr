# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project and CLI version resolution helpers."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Literal


def _git_available(root: Path) -> bool:
    return shutil.which("git") is not None and (root / ".git").exists()


def git_describe_version(root: Path) -> str | None:
    if shutil.which("git") is None:
        return None
    proc = subprocess.run(
        ["git", "describe", "--tags", "--always", "--dirty"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    v = proc.stdout.strip()
    return v or None


def changelog_version(root: Path) -> str | None:
    path = root / "debian" / "changelog"
    if not path.is_file():
        return None
    if shutil.which("dpkg-parsechangelog"):
        proc = subprocess.run(
            ["dpkg-parsechangelog", "-l", str(path), "-S", "Version"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            v = proc.stdout.strip()
            if v:
                return v.split(":", 1)[-1]
    first = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    if not first:
        return None
    m = re.match(r"\S+\s+\(([^)]+)\)", first[0])
    if not m:
        return None
    return m.group(1).split(":", 1)[-1]


def changelog_date(root: Path) -> str | None:
    """ISO date (YYYY-MM-DD) from the top debian/changelog stanza trailer."""
    path = root / "debian" / "changelog"
    if not path.is_file():
        return None
    raw = ""
    if shutil.which("dpkg-parsechangelog"):
        proc = subprocess.run(
            ["dpkg-parsechangelog", "-l", str(path), "-S", "Date"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            raw = proc.stdout.strip()
    if not raw:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith(" -- "):
                m = re.search(r"  ([A-Z][a-z]{2}, .+)$", line)
                if m:
                    raw = m.group(1).strip()
                break
    if not raw:
        return None
    try:
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def _paths_config_str(name: str) -> str | None:
    """Read a Meson-substituted string from paths_config (installed builds)."""
    try:
        from . import paths_config  # type: ignore
    except Exception:
        return None
    value = getattr(paths_config, name, None)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or value in {"@VERSION@", "@RELEASE_DATE@", "unknown"}:
        return None
    # Unsubstituted leftover from a broken configure.
    if value.startswith("@") and value.endswith("@"):
        return None
    return value


def version_file_version(root: Path) -> str | None:
    path = root / "VERSION"
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines:
        return None
    v = lines[0].strip()
    return v or None


def apply_version_modifiers(v: str) -> str:
    """Strip a leading v; wrap a non-semver token as 0.0.0-<token>."""
    v = v.strip()
    if v.startswith("v") and len(v) > 1:
        v = v[1:]
    if not v:
        return "0.0.0"
    core = v[: -len("-dirty")] if v.endswith("-dirty") else v
    if "." not in core:
        return f"0.0.0-{v}"
    return v


def rpm_compatible_version(v: str) -> str:
    """RPM Version cannot contain '-'."""
    return v.replace("-", "_")


def project_version(
    root: Path | None = None,
    *,
    source: Literal["git", "changelog"] | None = None,
    rpm: bool = False,
) -> str:
    """Project version: git describe, changelog, VERSION file, then 0.0.0."""
    from .shape import find_packagedir

    root = find_packagedir(root)
    git_ok = _git_available(root)
    if source is None:
        source = "git" if git_ok else "changelog"
    v: str | None = None
    if source == "git":
        v = git_describe_version(root)
    else:
        v = changelog_version(root)
    if not v:
        v = version_file_version(root)
    if not v:
        v = "0.0.0"
    v = apply_version_modifiers(v)
    if rpm:
        v = rpm_compatible_version(v)
    return v


def cli_root() -> Path:
    """Install prefix of this zfr tree (source: zfr/, installed: share/zephyr/zfr)."""
    libdir = Path(__file__).resolve().parent
    parent = libdir.parent
    if parent.name == "src":
        return parent.parent
    return parent


def cli_version(*, rpm: bool = False) -> str:
    """Version of the zfr CLI itself (not the project in cwd)."""
    root = cli_root()
    v = git_describe_version(root)
    if not v:
        v = _paths_config_str("VERSION")
    if not v:
        v = changelog_version(root)
    if not v:
        v = changelog_version(root.parent)
    if not v:
        v = version_file_version(root)
    if not v:
        v = "0.0.0"
    v = apply_version_modifiers(v)
    if rpm:
        v = rpm_compatible_version(v)
    return v


def cli_release_date() -> str | None:
    """Release date for this zfr CLI (Meson-baked, else latest changelog)."""
    baked = _paths_config_str("RELEASE_DATE")
    if baked:
        return baked
    root = cli_root()
    return changelog_date(root) or changelog_date(root.parent)


def _tool_version_line(label: str, argv: list[str], *, regex: str = r"(\d[\w.+-]*)") -> str | None:
    """Return ``Label X.Y`` from a tool's --version output, or None if missing."""
    if not argv or shutil.which(argv[0]) is None:
        return None
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (proc.stdout or "") + (proc.stderr or "")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    # Prefer an explicit "Version: …" line (OpenCC, …).
    for ln in lines:
        m = re.search(r"(?i)\bversion\s*[:=]\s*(\d[\w.+-]*)", ln)
        if m:
            return f"{label} {m.group(1)}"
    for ln in lines:
        m = re.search(regex, ln)
        if m:
            return f"{label} {m.group(1)}"
    return f"{label} {lines[0]}"


def cli_dependency_versions() -> list[str]:
    """Important runtime/tool versions for ``zfr --version``."""
    import sys

    lines: list[str] = []
    py = sys.version.split()[0]
    lines.append(f"Python {py}")
    for label, argv in (
        ("Meson", ["meson", "--version"]),
        ("Ninja", ["ninja", "--version"]),
        ("Asciidoctor", ["asciidoctor", "--version"]),
        ("Git", ["git", "--version"]),
        ("fdmux", ["fdmux", "--version"]),
        ("OpenCC", ["opencc", "--version"]),
        ("gettext", ["msgfmt", "--version"]),
    ):
        line = _tool_version_line(label, argv)
        if line:
            lines.append(line)
    return lines


def format_cli_version_banner() -> str:
    """Multi-line ``zfr --version`` text: version, release date, deps."""
    ver = cli_version()
    date = cli_release_date()
    head = f"zfr {ver}" + (f" ({date})" if date else "")
    deps = cli_dependency_versions()
    if not deps:
        return head
    return head + "\n" + "\n".join(deps)
