# SPDX-License-Identifier: AGPL-3.0-or-later
"""Packaging kind detection (what can be built under a project root)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# (kind, rel_dir, make_goals, out_rels for remote fetch)
MAKE_TARGETS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("rpm", "packaging/rpm", ("rpm", "srpm"), ()),
    ("mingw", "packaging/win32/mingw", ("local",), ("packaging/win32/mingw/out",)),
    ("innosetup", "packaging/win32/innosetup", ("local",), ("packaging/win32/innosetup/out",)),
    ("wix", "packaging/win32/wix", ("local",), ("packaging/win32/wix/out",)),
    ("macos", "packaging/macos", ("local",), ("packaging/macos/out",)),
    ("arch", "packaging/arch", ("local",), ("packaging/arch/out",)),
    ("freebsd", "packaging/freebsd", ("local",), ("packaging/freebsd/out",)),
)


@dataclass(frozen=True)
class PackagingKind:
    name: str
    """deb, rpm, npm, vsix, mingw, innosetup, wix, macos, arch, freebsd."""
    path: str = ""


def resolve_rpm_dir(root: Path) -> Path | None:
    for rel in ("packaging/rpm", "rpm"):
        d = root / rel
        if (d / "Makefile").is_file():
            return d
    return None


def target_meta(kind: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    for name, rel, goals, outs in MAKE_TARGETS:
        if name == kind:
            return rel, goals, outs
    raise KeyError(kind)


def detect_packaging_kinds(root: Path) -> list[PackagingKind]:
    """List packaging kinds available under *root* (detection order)."""
    root = root.resolve()
    found: list[PackagingKind] = []
    if (root / "debian" / "control").is_file():
        found.append(PackagingKind("deb", "debian/control"))
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        scripts = data.get("scripts") or {}
        package_script = str(scripts.get("package", ""))
        if "vsce package" in package_script:
            found.append(PackagingKind("vsix", "package.json"))
        else:
            found.append(PackagingKind("npm", "package.json"))
    for kind, rel, _goals, _outs in MAKE_TARGETS:
        if kind == "rpm":
            d = resolve_rpm_dir(root)
            if d is not None:
                found.append(PackagingKind("rpm", str(d.relative_to(root))))
            continue
        d = root / rel
        if (d / "Makefile").is_file():
            found.append(PackagingKind(kind, rel))
    return found
