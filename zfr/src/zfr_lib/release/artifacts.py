# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate version-scoped build outputs for install / upload / release."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .logutil import log1, quit, run

from .context import Context, ctx_reset_artifacts
from .detect import has_rpm_makefile, resolve_rpm_dir


_PACKAGING_OUT_DIRS = (
    "packaging/win32/mingw/out",
    "packaging/win32/innosetup/out",
    "packaging/win32/wix/out",
    "packaging/macos/out",
    "packaging/arch/out",
    "packaging/freebsd/out",
)


def artifact_name_matches_version(name: str, version: str) -> bool:
    """True when *name* embeds *version* as a version token (not a prefix of another).

    Examples for version ``2.8.16``: ``zephyr_mingw-2.8.16.exe`` matches;
    ``zephyr_mingw-2.8.1.exe`` does not.
    """
    import re

    if not version or not name:
        return False
    ver = re.escape(version)
    return bool(re.search(rf"(?:^|[_-]){ver}(?:[_.\-]|$)", name))


def find_packaging_out_artifacts(
    projectdir: Path | str,
    *,
    version: str,
    pkg: str = "",
) -> list[str]:
    """Collect version-scoped files under packaging/*/out.

    Only files whose basename embeds *version* (see
    :func:`artifact_name_matches_version`) are returned, so stale mingw/Inno
    builds for older versions are not attached to the current release.
    """
    projectdir = Path(projectdir)
    found: list[str] = []
    for rel in _PACKAGING_OUT_DIRS:
        out = projectdir / rel
        if not out.is_dir():
            continue
        for f in sorted(out.rglob("*")):
            if not f.is_file() or f.name.startswith("."):
                continue
            if not artifact_name_matches_version(f.name, version):
                continue
            found.append(str(f))
    return found


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


def find_attachments(
    project_type: str,
    projectdir: Path | str,
    version: str,
    pkg: str,
) -> list[str]:
    projectdir = Path(projectdir)
    found: list[str] = []
    if project_type == "vsix":
        for f in projectdir.glob(f"{pkg}-{version}.vsix"):
            if f.is_file():
                found.append(str(f))
    elif project_type == "nodejs":
        for f in projectdir.glob(f"{pkg}-{version}-dist.zip"):
            if f.is_file():
                found.append(str(f))
    return found


def _control_packages(control: Path, field: str) -> list[str]:
    pkgs: list[str] = []
    if not control.is_file():
        return pkgs
    prefix = f"{field}:"
    with control.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith(prefix):
                pkg = line.split(":", 1)[1].strip()
                if pkg:
                    pkgs.append(pkg)
    return pkgs


def find_deb_files(
    project_dir: Path | str,
    output_dir: Path | str,
    version: str,
) -> list[str]:
    """Find .deb files for all Package: names in debian/control (incl. -dbgsym)."""
    project_dir = Path(project_dir)
    output_dir = Path(output_dir)
    found: list[str] = []
    for pkg in _control_packages(project_dir / "debian" / "control", "Package"):
        for f in output_dir.glob(f"{pkg}_{version}_*.deb"):
            if f.is_file():
                found.append(str(f))
        for f in output_dir.glob(f"{pkg}-dbgsym_{version}_*.deb"):
            if f.is_file():
                found.append(str(f))
    return found


def find_artifacts_dir(dir_path: Path | str) -> Path | None:
    d = Path(dir_path)
    while True:
        art = d / "artifacts"
        if art.is_dir():
            return art
        parent = d.parent
        if parent == d:
            return None
        d = parent


def find_changes_file(
    project_dir: Path | str,
    output_dir: Path | str,
    version: str,
) -> str:
    project_dir = Path(project_dir)
    output_dir = Path(output_dir)
    for pkg in _control_packages(project_dir / "debian" / "control", "Source"):
        matches = sorted(
            str(f)
            for f in output_dir.glob(f"{pkg}_{version}_*.changes")
            if f.is_file()
        )
        if matches:
            return matches[0]
    return ""


def _rpm_artifact_topdirs(projectdir: Path) -> list[Path]:
    """Directories that may hold RPMS/SRPMS/SOURCES (read-only discovery).

    Local builds land under ``%_topdir`` ($HOME/rpmbuild). Remote builds fetch
    into ``packaging/rpm/out`` (or legacy ``rpm/out``) and may add new files
    into ``%_topdir`` without overwriting or deleting existing ones.
    """
    dirs: list[Path] = [rpm_topdir()]
    rpm_dir = resolve_rpm_dir(projectdir)
    if rpm_dir is not None:
        dirs.append(rpm_dir / "out")
    # Legacy leftover; discovery only (ZL030 when present).
    dirs.append(projectdir / "rpmbuild")
    return dirs


def find_rpm_artifacts(
    projectdir: Path | str,
    pkg: str,
    version: str,
) -> list[str]:
    projectdir = Path(projectdir)
    found: list[str] = []
    for topdir in _rpm_artifact_topdirs(projectdir):
        if not topdir.is_dir():
            continue
        rpms = topdir / "RPMS"
        if rpms.is_dir():
            for arch_dir in rpms.iterdir():
                if not arch_dir.is_dir():
                    continue
                for f in arch_dir.glob(f"{pkg}-{version}-*.rpm"):
                    if f.is_file():
                        found.append(str(f))
        srpm = topdir / "SRPMS"
        if srpm.is_dir():
            for f in srpm.glob(f"{pkg}-{version}-*.rpm"):
                if f.is_file():
                    found.append(str(f))
    # Prefer %_topdir hits; drop duplicates by basename keeping first.
    seen: set[str] = set()
    uniq: list[str] = []
    for p in found:
        name = Path(p).name
        if name in seen:
            continue
        seen.add(name)
        uniq.append(p)
    return uniq


def find_dist_tarball(
    projectdir: Path | str,
    pkg: str,
    version: str,
) -> str | None:
    projectdir = Path(projectdir)
    names = (
        f"{pkg}-{version}.tar.xz",
        f"{pkg}-{version}.tar.gz",
        f"{pkg}_{version}.orig.tar.xz",
        f"{pkg}_{version}.orig.tar.gz",
    )
    for topdir in _rpm_artifact_topdirs(projectdir):
        sources = topdir / "SOURCES"
        for name in names:
            f = sources / name
            if f.is_file():
                return str(f)
    return None


def find_debian_source_tarball(
    project_dir: Path | str,
    output_dir: Path | str,
    version: str,
) -> str:
    """Debian upstream/native source archive for the release tarball slot."""
    project_dir = Path(project_dir)
    output_dir = Path(output_dir)
    suffixes = [
        f"_{version}.tar.xz",
        f"_{version}.tar.gz",
        f"_{version}.orig.tar.xz",
        f"_{version}.orig.tar.gz",
    ]
    for pkg in _control_packages(project_dir / "debian" / "control", "Source"):
        for suf in suffixes:
            f = output_dir / f"{pkg}{suf}"
            if f.is_file():
                return str(f)
    return ""


def find_dsc_files(
    project_dir: Path | str,
    output_dir: Path | str,
    version: str,
) -> list[str]:
    """Debian .dsc and debian.tar.* (not upstream source tarballs)."""
    project_dir = Path(project_dir)
    output_dir = Path(output_dir)
    found: list[str] = []
    suffixes = [
        f"_{version}.dsc",
        f"_{version}.debian.tar.xz",
        f"_{version}.debian.tar.gz",
    ]
    for pkg in _control_packages(project_dir / "debian" / "control", "Source"):
        for suf in suffixes:
            f = output_dir / f"{pkg}{suf}"
            if f.is_file():
                found.append(str(f))
    return found


def _has_src_rpm(rpm_artifacts: list[str]) -> bool:
    return any("/SRPMS/" in p for p in rpm_artifacts)


def have_build_artifacts(
    project_type: str,
    projectdir: Path | str,
    version: str,
    pkg: str,
    builddir: Path | str | None,
) -> bool:
    """True if version-scoped build outputs already exist (for --upload reuse)."""
    projectdir = Path(projectdir)
    if project_type == "debian":
        if builddir is None:
            return False
        if not find_deb_files(projectdir, builddir, version):
            return False
    elif project_type in ("vsix", "nodejs"):
        if not find_attachments(project_type, projectdir, version, pkg):
            return False
    else:
        return False

    if has_rpm_makefile(projectdir):
        if not find_rpm_artifacts(projectdir, pkg, version):
            return False
    return True


def step_collect_artifacts(ctx: Context) -> None:
    """Collect release attachments into ctx.attachments / deb_files / tarball."""
    ctx_reset_artifacts(ctx)

    rpm_artifacts: list[str] = []
    if has_rpm_makefile(ctx.projectdir):
        rpm_artifacts = find_rpm_artifacts(
            ctx.projectdir, ctx.pkgname, ctx.version
        )

    if ctx.project_type == "debian":
        assert ctx.builddir is not None
        ctx.deb_files = find_deb_files(ctx.projectdir, ctx.builddir, ctx.version)
        ctx.attachments.extend(ctx.deb_files)
        ctx.attachments.extend(
            find_dsc_files(ctx.projectdir, ctx.builddir, ctx.version)
        )

    ctx.attachments.extend(
        find_attachments(
            ctx.project_type, ctx.projectdir, ctx.version, ctx.pkgname
        )
    )
    ctx.attachments.extend(rpm_artifacts)
    ctx.attachments.extend(
        find_packaging_out_artifacts(
            ctx.projectdir, version=ctx.version, pkg=ctx.pkgname
        )
    )

    tarball = ""
    if ctx.project_type == "debian" and ctx.builddir is not None:
        tarball = find_debian_source_tarball(
            ctx.projectdir, ctx.builddir, ctx.version
        )

    if not tarball and rpm_artifacts and not _has_src_rpm(rpm_artifacts):
        found = find_dist_tarball(ctx.projectdir, ctx.pkgname, ctx.version)
        if found:
            tarball = found
            log1(f"Using RPM dist tarball {tarball}")

    if not tarball:
        log1("Creating source tarball preserving original sources")
        tarball = f"{ctx.pkgname}-{ctx.version}.tar.gz"
        run(
            "git",
            "archive",
            "--format=tar.gz",
            f"--prefix={ctx.pkgname}-{ctx.version}/",
            "-o",
            tarball,
            "HEAD",
        )

    ctx.tarball = tarball
    ctx.attachments = [a for a in ctx.attachments if a != ctx.tarball]

    if not ctx.attachments and not ctx.tarball:
        quit("No build artifacts produced.")
    log1(f"Release source tarball: {ctx.tarball}")
    log1(f"Attachments: {' '.join(ctx.attachments)}")
