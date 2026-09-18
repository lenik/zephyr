# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared Debian/Meson field parsers used by lint, dist, about, and ize."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


def rpm_topdir() -> Path:
    """RPM ``%_topdir``: ``$HOME/rpmbuild`` by default (``~/.rpmmacros`` may override)."""
    if shutil.which("rpm"):
        try:
            proc = subprocess.run(
                ["rpm", "--eval", "%{_topdir}"],
                check=True,
                capture_output=True,
                text=True,
            )
            val = proc.stdout.strip()
            if val and not val.startswith("%"):
                return Path(val).expanduser()
        except (OSError, subprocess.CalledProcessError):
            pass
    return Path.home() / "rpmbuild"


_LOCAL_TOPDIR_RE = re.compile(
    r"^TOPDIR\s*\??=\s*\$\(abspath\s+\$\(SRCDIR\)/rpmbuild\)\s*$",
    re.M,
)
_TOPDIR_BLOCK = (
    "# RPM %_topdir: $HOME/rpmbuild by default (override in ~/.rpmmacros).\n"
    "# Override per build: make TOPDIR=/other/rpmbuild\n"
    "TOPDIR  ?= $(shell rpm --eval '%{_topdir}' 2>/dev/null)\n"
    "ifeq ($(strip $(TOPDIR)),)\n"
    "TOPDIR  := $(HOME)/rpmbuild\n"
    "endif"
)
_CLEAN_BLOCK = (
    "clean:\n"
    "\trm -f $(TOPDIR)/SPECS/$(NAME).spec\n"
    "\trm -f $(TOPDIR)/SOURCES/$(NAME)-*.tar.*\n"
    "\trm -f $(TOPDIR)/SRPMS/$(NAME)-*.src.rpm\n"
    "\trm -f $(TOPDIR)/RPMS/*/$(NAME)-*.rpm\n"
    "\trm -rf $(TOPDIR)/BUILD/$(NAME)-*\n"
    "\trm -rf $(TOPDIR)/BUILDROOT/$(NAME)-*\n"
)
_OLD_CLEAN_RE = re.compile(
    r"^clean:\n\trm -rf \$\(TOPDIR\)\s*$",
    re.M,
)


def makefile_uses_local_rpmbuild(text: str) -> bool:
    """True when *rpm/Makefile* pins TOPDIR to ``<project>/rpmbuild``."""
    return bool(_LOCAL_TOPDIR_RE.search(text)) or bool(
        re.search(r"TOPDIR\s*\??=\s*.*\$\(SRCDIR\)/rpmbuild", text)
    )


def migrate_rpm_makefile_topdir(text: str) -> str | None:
    """Rewrite project-local TOPDIR/clean to %_topdir; return new text or None."""
    new = text
    changed = False
    if _LOCAL_TOPDIR_RE.search(new) or re.search(
        r"^TOPDIR\s*\??=\s*\$\(abspath\s+\$\(SRCDIR\)/rpmbuild\)", new, re.M
    ):
        new = re.sub(
            r"(?m)^TOPDIR\s*\??=\s*\$\(abspath\s+\$\(SRCDIR\)/rpmbuild\)\s*\n",
            _TOPDIR_BLOCK + "\n",
            new,
            count=1,
        )
        changed = True
    if _OLD_CLEAN_RE.search(new):
        new = _OLD_CLEAN_RE.sub(_CLEAN_BLOCK, new, count=1)
        changed = True
    elif re.search(r"(?m)^clean:\n\trm -rf \$\(TOPDIR\)\s*$", new):
        new = re.sub(
            r"(?m)^clean:\n\trm -rf \$\(TOPDIR\)\s*$",
            _CLEAN_BLOCK,
            new,
            count=1,
        )
        changed = True
    return new if changed else None


def rpm_dir(root: Path) -> Path:
    """RPM packaging directory under ``packaging/rpm/``."""
    return root / "packaging" / "rpm"


def legacy_rpm_dir(root: Path) -> Path:
    """Pre-2.7.8 layout: top-level ``rpm/`` next to debian/."""
    return root / "rpm"


def resolve_rpm_dir(root: Path) -> Path:
    """Return the RPM packaging dir (prefers ``packaging/rpm/``, falls back to ``rpm/``)."""
    new = rpm_dir(root)
    if new.is_dir():
        return new
    old = legacy_rpm_dir(root)
    if old.is_dir():
        return old
    return new


def migrate_legacy_rpm_dir(root: Path) -> bool:
    """Move legacy ``rpm/`` to ``packaging/rpm/``; fix Makefile SRCDIR. Return True if moved."""
    legacy = legacy_rpm_dir(root)
    dest = rpm_dir(root)
    if not legacy.is_dir() or dest.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    legacy.rename(dest)
    makefile = dest / "Makefile"
    if makefile.is_file():
        text = makefile.read_text(encoding="utf-8", errors="ignore")
        new = text.replace(
            "SRCDIR  := $(abspath ..)",
            "SRCDIR  := $(abspath ../..)",
        )
        new = new.replace(
            "Usage (from rpm/):",
            "Usage (from packaging/rpm/):",
        )
        if new != text:
            makefile.write_text(new, encoding="utf-8")
    return True


def parse_control_stanzas(text: str) -> list[dict[str, str]]:
    stanzas: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    key: str | None = None
    for line in text.splitlines():
        if not line.strip():
            if cur:
                stanzas.append(cur)
                cur = {}
                key = None
            continue
        if key and (line.startswith(" ") or line.startswith("\t")):
            cur[key] += "\n" + line.strip()
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            cur[key] = val.strip()
    if cur:
        stanzas.append(cur)
    return stanzas


def meson_project_fields(root: Path) -> dict[str, str]:
    meson = root / "meson.build"
    out: dict[str, str] = {}
    if not meson.is_file():
        return out
    text = meson.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"project\s*\(\s*['\"]([^'\"]+)['\"]", text)
    if m:
        out["name"] = m.group(1)
    m = re.search(r"license\s*:\s*['\"]([^'\"]+)['\"]", text)
    if m:
        out["license"] = m.group(1)
    return out


# Names used throughout the existing call sites (both spellings).
_parse_control_stanzas = parse_control_stanzas
_parse_control_stanzas = parse_control_stanzas
_meson_project_fields = meson_project_fields
_meson_project_fields = meson_project_fields
