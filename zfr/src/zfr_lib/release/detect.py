# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project type / version / package name detection."""

from __future__ import annotations

import json
from pathlib import Path

from .logutil import log1, quit

from .context import Context


def detect_project_type(projectdir: Path | str) -> str | None:
    projectdir = Path(projectdir)

    if (projectdir / "debian" / "control").is_file():
        return "debian"

    pkg_json = projectdir / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        package_script = ""
        scripts = data.get("scripts") if isinstance(data, dict) else None
        if isinstance(scripts, dict):
            package_script = str(scripts.get("package") or "")
        if "vsce package" in package_script:
            return "vsix"
        return "nodejs"

    return None


def get_version(project_type: str, projectdir: Path | str) -> str:
    projectdir = Path(projectdir)
    if project_type == "debian":
        changelog = projectdir / "debian" / "changelog"
        if not changelog.is_file():
            quit("debian/changelog not found.")
        with changelog.open(encoding="utf-8") as fh:
            first = fh.readline()
        # package (version) ...
        if "(" in first and ")" in first:
            return first.split("(", 1)[1].split(")", 1)[0]
        return ""
    if project_type in ("vsix", "nodejs"):
        pkg_json = projectdir / "package.json"
        if not pkg_json.is_file():
            quit("package.json not found.")
        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        return str(data.get("version") or "")
    return ""


def get_package_name(project_type: str, projectdir: Path | str) -> str:
    projectdir = Path(projectdir)
    if project_type == "debian":
        control = projectdir / "debian" / "control"
        pkg = ""
        if control.is_file():
            with control.open(encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("Source:"):
                        pkg = line.split(":", 1)[1].strip()
                        break
        return pkg or projectdir.name
    if project_type in ("vsix", "nodejs"):
        data = json.loads(
            (projectdir / "package.json").read_text(encoding="utf-8")
        )
        return str(data.get("name") or "")
    return ""


def make_build_dir(project_type: str, projectdir: Path | str) -> Path:
    projectdir = Path(projectdir)
    if project_type == "debian":
        return projectdir.parent
    return projectdir


def has_rpm_makefile(projectdir: Path | str) -> bool:
    return resolve_rpm_dir(projectdir) is not None


def resolve_rpm_dir(projectdir: Path | str) -> Path | None:
    """Return ``packaging/rpm`` or legacy ``rpm`` if a Makefile is present."""
    projectdir = Path(projectdir)
    for rel in ("packaging/rpm", "rpm"):
        d = projectdir / rel
        if (d / "Makefile").is_file():
            return d
    return None


def step_detect(ctx: Context) -> None:
    """Fill project_type, version, pkgname, tag, builddir."""
    detected = detect_project_type(ctx.projectdir)
    if not detected:
        quit("Could not detect project type (debian/vsix/nodejs).")
    ctx.project_type = detected

    ctx.version = get_version(ctx.project_type, ctx.projectdir)
    if not ctx.version:
        quit("Could not determine version.")

    ctx.pkgname = get_package_name(ctx.project_type, ctx.projectdir)
    if not ctx.pkgname:
        ctx.pkgname = ctx.projectdir.name

    ctx.tag = f"v{ctx.version}"
    ctx.builddir = make_build_dir(ctx.project_type, ctx.projectdir)

    log1(f"Project type: {ctx.project_type}")
    log1(f"Version: {ctx.version}  Package: {ctx.pkgname}  Tag: {ctx.tag}")
    log1(f"Build directory: {ctx.builddir}")
