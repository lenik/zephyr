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

from . import (
    _is_zfr_cli_package,
    _is_zfr_meta_repo,
    find_project_dir,
    project_version,
)
from .cli import register_command
from .i18n import _
from .packaging import _meson_project_fields, _parse_control_stanzas, rpm_topdir

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
        help=_(
            "write the archive into DIR (default: meson-dist, or "
            "%%_topdir/SOURCES with --rpm; usually $HOME/rpmbuild)"
        ),
    )
    p.add_argument(
        "-b",
        "--builddir",
        type=Path,
        metavar="DIR",
        help=_(
            "Meson build directory (default: /build when it matches this "
            "source tree, else <project>/build)"
        ),
    )
    p.add_argument(
        "-f",
        "--format",
        dest="fmt",
        choices=tuple(_FORMATS),
        default="xz",
        help=_("archive format (default: xz)"),
    )
    p.add_argument(
        "--rpm",
        action="store_true",
        help=_(
            "name the archive NAME-VERSION.tar.xz and write it to "
            "%%_topdir/SOURCES ($HOME/rpmbuild by default; ~/.rpmmacros) "
            "unless -o is given"
        ),
    )
    p.add_argument(
        "--allow-dirty",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=_("pass --allow-dirty to meson dist (default: allow)"),
    )
    p.add_argument(
        "--tests",
        action="store_true",
        help=_("run tests during meson dist (default: --no-tests)"),
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



def _git_tracks(root: Path, relpath: str) -> bool:
    """True when *relpath* is tracked in the git checkout at *root*."""
    if shutil.which("git") is None:
        return False
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relpath],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


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
        outdir = (rpm_topdir() / "SOURCES").resolve()
    else:
        outdir = None

    git_root = _git_toplevel(root)
    archive_root = root
    if (
        _is_zfr_cli_package(root)
        and git_root is not None
        and _is_zfr_meta_repo(git_root)
    ):
        # Meta-package tarball must include sibling language templates.
        archive_root = git_root
        use_meson = False
    else:
        use_meson = git_root is not None and git_root.resolve() == root.resolve()

    # After `zfr ize`, meson.build is often untracked until the user commits.
    # meson dist then fails ("git returned a failure"); fall back to a
    # project-tree archive so `zfr release -lI` RPM builds still work.
    if use_meson and not _git_tracks(root, "meson.build"):
        print(
            "meson.build not tracked in git; packing project tree "
            "(commit ize results to use meson dist)",
            file=sys.stderr,
        )
        use_meson = False

    if use_meson:
        bdir = resolve_builddir(root, builddir)
        ensure_meson_setup(root, bdir)
        try:
            produced = _meson_dist(
                bdir, fmt=fmt, allow_dirty=allow_dirty, tests=tests
            )
        except SystemExit as exc:
            print(
                f"{exc}; falling back to project-tree archive",
                file=sys.stderr,
            )
            use_meson = False
        else:
            dest = produced if outdir is None else outdir / tarball_name
            if outdir is None and produced.name != tarball_name:
                dest = produced.with_name(tarball_name)
            dest = _place_archive(produced, dest)
            print(dest, flush=True)
            return 0

    print(
        f"meson dist would archive {git_root or '(no git)'}; "
        f"packing {archive_root}",
        file=sys.stderr,
    )
    if outdir is None:
        bdir = resolve_builddir(root, builddir)
        outdir = bdir / "meson-dist"
    dest = outdir / tarball_name
    _directory_archive(archive_root, dest, f"{name}-{version}", fmt=fmt)
    print(dest, flush=True)
    return 0

NAME = "dist"
HELP = _("build a source tarball (meson dist, or this project only)")
DESCRIPTION = _(
    "Build a source archive of the current zephyr project "
    "(walks from cwd toward parent directories). Uses meson dist when "
    "this directory is the git project root; otherwise packs this "
    "project only so nested language templates do not ship the parent "
    "meta-repo. Prints the archive path on stdout."
)

add_arguments = add_dist_arguments


def run(args: argparse.Namespace) -> int:
    return cmd_dist(
        output=args.output,
        builddir=args.builddir,
        fmt=args.fmt,
        rpm=args.rpm,
        allow_dirty=args.allow_dirty,
        tests=args.tests,
    )


def register(sub: argparse._SubParsersAction) -> None:
    register_command(sub, NAME, help=HELP, description=DESCRIPTION, add_arguments=add_arguments, run=run)
