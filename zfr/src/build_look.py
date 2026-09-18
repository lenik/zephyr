# SPDX-License-Identifier: AGPL-3.0-or-later
"""DESTDIR install preview (replaces scripts/look.sh / meson run_target look)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from lib import find_project_dir


def look_install(
    root: Path | None = None,
    *,
    builddir: Path | None = None,
    depth: int | None = None,
) -> int:
    """Install into a temp DESTDIR and print a tree preview.

    *depth* limits ``tree -L`` / walk depth when set; ``None`` means unlimited
    (default for ``ninja look`` / ``zfr build --look``).
    """
    if root is None:
        env_root = os.environ.get("MESON_SOURCE_ROOT") or os.environ.get("SOURCE_ROOT")
        root = Path(env_root).resolve() if env_root else find_project_dir()
    root = root.resolve()

    if builddir is None:
        env_build = os.environ.get("MESON_BUILD_ROOT") or os.environ.get("BUILD_ROOT")
        if env_build:
            builddir = Path(env_build).resolve()
        else:
            builddir = root / "build"
    else:
        builddir = builddir.expanduser()
        if not builddir.is_absolute():
            builddir = (root / builddir).resolve()

    if not (builddir / "build.ninja").is_file() and not (builddir / "Makefile").is_file():
        if not builddir.is_dir():
            print(f"zfr build --look: build dir not found: {builddir}", flush=True)
            return 1

    meson = shutil.which("meson")
    if not meson:
        print("zfr build --look: meson not found", flush=True)
        return 1

    if depth is not None and depth < 1:
        print(f"zfr build --look: invalid look level {depth}", flush=True)
        return 2

    tmpdir = Path(tempfile.mkdtemp(prefix="zfr-look-"))
    try:
        proc = subprocess.run(
            [meson, "install", "-C", str(builddir)],
            env={**os.environ, "DESTDIR": str(tmpdir)},
            check=False,
        )
        if proc.returncode != 0:
            print(f"zfr build --look: meson install failed ({proc.returncode})", flush=True)
            return proc.returncode

        tree = shutil.which("tree")
        if tree:
            cmd = [tree, "-I", "po|__pycache__", str(tmpdir)]
            if depth is not None:
                cmd[1:1] = ["-L", str(depth)]
            subprocess.run(cmd, check=False)
        else:
            for dirpath, dirnames, filenames in os.walk(tmpdir):
                rel = Path(dirpath).relative_to(tmpdir)
                parts = rel.parts
                if parts and parts[0] == "po":
                    dirnames[:] = []
                    continue
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                if depth is not None:
                    if len(parts) > depth:
                        dirnames[:] = []
                        continue
                    if len(parts) == depth:
                        dirnames[:] = []
                indent = "  " * len(parts)
                name = parts[-1] if parts else "."
                print(f"{indent}{name}/" if parts else str(tmpdir))
                # Match tree -L: show files at the max depth, but do not descend.
                show_files = depth is None or len(parts) <= depth
                if show_files:
                    for fn in sorted(filenames):
                        print(f"{indent}  {fn}")

        man_pages = sorted({p.resolve() for p in tmpdir.rglob("*.1") if "man" in p.parts})
        mo_files = sorted(tmpdir.rglob("*.mo"))
        zfr_root = None
        for cand in tmpdir.rglob("zephyr/zfr"):
            if cand.is_dir():
                zfr_root = cand
                break
        zfr_files = sorted(p for p in zfr_root.rglob("*") if p.is_file()) if zfr_root else []
        print(flush=True)
        print(
            f"look summary: manpages={len(man_pages)}  locale_mo={len(mo_files)}  "
            f"zephyr/zfr_files={len(zfr_files)}",
            flush=True,
        )
        if len(man_pages) == 0:
            print("look warning: no man pages installed under DESTDIR", flush=True)
        if len(mo_files) == 0:
            print("look warning: no gettext .mo catalogs installed under DESTDIR", flush=True)
        if zfr_root is None or len(zfr_files) == 0:
            print("look warning: share/.../zephyr/zfr looks incomplete", flush=True)
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def look_main(argv: list[str] | None = None) -> int:
    args = list(__import__("sys").argv[1:] if argv is None else argv)
    root = Path(args[0]).resolve() if args else None
    builddir = Path(args[1]).resolve() if len(args) > 1 else None
    return look_install(root, builddir=builddir)


if __name__ == "__main__":
    raise SystemExit(look_main())
