# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr dist — source tarball for meson and RPM."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import find_project_dir, project_version
from .commands import _meson_project_fields, _parse_control_stanzas

_FORMATS = {
    "xz": ("xztar", ".tar.xz"),
    "gz": ("gztar", ".tar.gz"),
    "zip": ("zip", ".zip"),
}

_SKIP_DIR_NAMES = {
    "build",
    "rpmbuild",
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".cursor",
    ".vscode",
    "__pycache__",
    "meson-info",
    "meson-logs",
    "meson-private",
}

_DEBIAN_SKIP_NAMES = {
    "build",
    "zephyr",
    ".debhelper",
    "files",
}


def add_dist_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="DIR",
        help="write the archive into DIR (default: meson-dist, or "
        "rpmbuild/SOURCES with --rpm)",
    )
    p.add_argument(
        "-b",
        "--builddir",
        type=Path,
        metavar="DIR",
        help="Meson build directory (default: /build when it matches this "
        "source tree, else <project>/build)",
    )
    p.add_argument(
        "-f",
        "--format",
        dest="fmt",
        choices=tuple(_FORMATS),
        default="xz",
        help="archive format (default: xz)",
    )
    p.add_argument(
        "--rpm",
        action="store_true",
        help="name the archive NAME-VERSION.tar.xz and write it to "
        "rpmbuild/SOURCES unless -o is given",
    )
    p.add_argument(
        "--allow-dirty",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="pass --allow-dirty to meson dist (default: allow)",
    )
    p.add_argument(
        "--tests",
        action="store_true",
        help="run tests during meson dist (default: --no-tests)",
    )


def _project_name(root: Path) -> str:
    meson = _meson_project_fields(root)
    control = root / "debian" / "control"
    source = ""
    if control.is_file():
        text = control.read_text(encoding="utf-8", errors="ignore")
        stanzas = _parse_control_stanzas(text)
        if stanzas:
            source = stanzas[0].get("Source") or ""
    return source or meson.get("name") or root.name


def _git_toplevel(root: Path) -> Path | None:
    if shutil.which("git") is None:
        return None
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    return Path(text) if text else None


def _meson_source_of(builddir: Path) -> Path | None:
    info = builddir / "meson-info" / "meson-info.json"
    if not info.is_file():
        return None
    try:
        data = json.loads(info.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    src = (data.get("directories") or {}).get("source")
    return Path(src) if src else None


def _try_project_dir(start: Path) -> Path | None:
    try:
        return find_project_dir(start)
    except SystemExit:
        return None


def resolve_root(
    workdir: Path | None,
    builddir: Path | None,
) -> Path:
    """Project root: walk from cwd, else Meson builddir source (ninja srcdist)."""
    found = _try_project_dir(workdir or Path.cwd())
    if found is not None:
        return found
    candidates: list[Path] = []
    if builddir is not None:
        candidates.append(builddir.expanduser().resolve())
    candidates.append(Path("/build"))
    for bdir in candidates:
        src = _meson_source_of(bdir)
        if src is not None:
            found = _try_project_dir(src)
            if found is not None:
                return found
    return find_project_dir(workdir)


def resolve_builddir(root: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    default = Path("/build")
    src = _meson_source_of(default)
    if src is not None and src.resolve() == root.resolve():
        return default
    return (root / "build").resolve()


def ensure_meson_setup(root: Path, builddir: Path) -> None:
    if shutil.which("meson") is None:
        raise SystemExit("zfr dist: meson not found on PATH")
    info = builddir / "meson-info" / "meson-info.json"
    cmd = ["meson", "setup"]
    if info.is_file():
        cmd.append("--reconfigure")
    cmd.extend([str(builddir), str(root)])
    print(f"meson setup {builddir}", file=sys.stderr)
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise SystemExit(f"zfr dist: meson setup failed ({proc.returncode})")


def _meson_dist(
    builddir: Path,
    *,
    fmt: str,
    allow_dirty: bool,
    tests: bool,
) -> Path:
    meson_fmt, suffix = _FORMATS[fmt]
    cmd = ["meson", "dist", "-C", str(builddir), f"--formats={meson_fmt}"]
    if allow_dirty:
        cmd.append("--allow-dirty")
    if not tests:
        cmd.append("--no-tests")
    print(" ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise SystemExit(f"zfr dist: meson dist failed ({proc.returncode})")
    dist_dir = builddir / "meson-dist"
    if not dist_dir.is_dir():
        raise SystemExit(f"zfr dist: missing {dist_dir}")
    matches = sorted(
        [p for p in dist_dir.iterdir() if p.is_file() and p.name.endswith(suffix)],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise SystemExit(f"zfr dist: no {suffix} in {dist_dir}")
    return matches[0]


def _copy_ignore(directory: str, names: list[str]) -> set[str]:
    ignored = {n for n in names if n in _SKIP_DIR_NAMES}
    if Path(directory).name == "debian":
        ignored.update(n for n in names if n in _DEBIAN_SKIP_NAMES)
    return ignored


def _directory_archive(
    root: Path,
    dest: Path,
    inner_dir: str,
    *,
    fmt: str,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    with tempfile.TemporaryDirectory(prefix="zfr-dist-") as tmp:
        inner = Path(tmp) / inner_dir
        shutil.copytree(
            root,
            inner,
            ignore=_copy_ignore,
            symlinks=True,
        )
        if fmt == "zip":
            archive = shutil.make_archive(
                str(dest.with_suffix("")),
                "zip",
                root_dir=tmp,
                base_dir=inner_dir,
            )
            produced = Path(archive)
            if produced.resolve() != dest.resolve():
                shutil.move(str(produced), dest)
            return
        compress = "J" if fmt == "xz" else "z"
        proc = subprocess.run(
            ["tar", "-C", tmp, f"-c{compress}f", str(dest), inner_dir],
            check=False,
        )
        if proc.returncode != 0:
            raise SystemExit("zfr dist: tar (write archive) failed")


def _place_archive(produced: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if produced.resolve() != dest.resolve():
        shutil.copy2(produced, dest)
    return dest


def cmd_dist(
    *,
    output: Path | None = None,
    builddir: Path | None = None,
    fmt: str = "xz",
    rpm: bool = False,
    allow_dirty: bool = True,
    tests: bool = False,
    workdir: Path | None = None,
) -> int:
    """Build a source tarball (meson dist, or a project-only archive)."""
    if fmt not in _FORMATS:
        raise SystemExit(f"zfr dist: unknown format {fmt!r} (xz, gz, zip)")
    root = resolve_root(workdir, builddir)
    name = _project_name(root)
    version = project_version(root)
    suffix = _FORMATS[fmt][1]
    tarball_name = f"{name}-{version}{suffix}"

    outdir: Path | None
    if output is not None:
        outdir = output.expanduser().resolve()
    elif rpm:
        outdir = (root / "rpmbuild" / "SOURCES").resolve()
    else:
        outdir = None

    git_root = _git_toplevel(root)
    use_meson = git_root is not None and git_root.resolve() == root.resolve()

    if use_meson:
        bdir = resolve_builddir(root, builddir)
        ensure_meson_setup(root, bdir)
        produced = _meson_dist(
            bdir, fmt=fmt, allow_dirty=allow_dirty, tests=tests
        )
        dest = produced if outdir is None else outdir / tarball_name
        if outdir is None and produced.name != tarball_name:
            dest = produced.with_name(tarball_name)
        dest = _place_archive(produced, dest)
        print(dest, flush=True)
        return 0

    print(
        f"meson dist would archive {git_root or '(no git)'}; packing {root} only",
        file=sys.stderr,
    )
    if outdir is None:
        bdir = resolve_builddir(root, builddir)
        outdir = bdir / "meson-dist"
    dest = outdir / tarball_name
    _directory_archive(root, dest, f"{name}-{version}", fmt=fmt)
    print(dest, flush=True)
    return 0
