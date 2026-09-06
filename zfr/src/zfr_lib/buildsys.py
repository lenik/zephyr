# SPDX-License-Identifier: AGPL-3.0-or-later
"""Detect build systems (meson, cmake, autotools, …) and compile."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BuildSystem:
    name: str
    """Canonical id: meson, cmake, autotools, cargo, go, npm, make."""
    detail: str = ""


def detect_build_system(root: Path) -> BuildSystem | None:
    """Return the primary build system for *root*, or None if unknown."""
    root = root.resolve()
    if (root / "meson.build").is_file():
        return BuildSystem("meson", "meson.build")
    if (root / "CMakeLists.txt").is_file():
        return BuildSystem("cmake", "CMakeLists.txt")
    if (root / "configure").is_file() and os.access(root / "configure", os.X_OK):
        return BuildSystem("autotools", "configure")
    if (root / "configure.ac").is_file() or (root / "configure.in").is_file():
        return BuildSystem("autotools", "configure.ac")
    if (root / "Cargo.toml").is_file():
        return BuildSystem("cargo", "Cargo.toml")
    if (root / "go.mod").is_file():
        return BuildSystem("go", "go.mod")
    pkg = root / "package.json"
    if pkg.is_file():
        return BuildSystem("npm", "package.json")
    if (root / "Makefile").is_file() or (root / "makefile").is_file():
        return BuildSystem("make", "Makefile")
    return None


def _run(cmd: list[str], *, cwd: Path, dry_run: bool = False) -> None:
    print("+", " ".join(cmd), flush=True)
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def _which(*names: str) -> str | None:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def build_project(
    root: Path,
    *,
    builddir: Path | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> BuildSystem:
    """Detect and build *root*. Raises SystemExit on failure / unknown system."""
    root = root.resolve()
    sysinfo = detect_build_system(root)
    if sysinfo is None:
        raise SystemExit(f"zfr build: no known build system under {root}")

    builddir = (builddir or (root / "build")).resolve()
    name = sysinfo.name
    print(f"zfr build: detected {name} ({sysinfo.detail})", flush=True)

    if name == "meson":
        meson = _which("meson")
        if not meson:
            raise SystemExit("zfr build: meson not found in PATH")
        if not (builddir / "build.ninja").is_file() and not (builddir / "Makefile").is_file():
            _run([meson, "setup", str(builddir)], cwd=root, dry_run=dry_run)
        compile_cmd = [meson, "compile", "-C", str(builddir)]
        if verbose:
            compile_cmd.append("-v")
        _run(compile_cmd, cwd=root, dry_run=dry_run)
        return sysinfo

    if name == "cmake":
        cmake = _which("cmake")
        if not cmake:
            raise SystemExit("zfr build: cmake not found in PATH")
        builddir.mkdir(parents=True, exist_ok=True)
        if not (builddir / "CMakeCache.txt").is_file():
            _run([cmake, "-S", str(root), "-B", str(builddir)], cwd=root, dry_run=dry_run)
        build_cmd = [cmake, "--build", str(builddir)]
        if verbose:
            build_cmd.append("--verbose")
        _run(build_cmd, cwd=root, dry_run=dry_run)
        return sysinfo

    if name == "autotools":
        if not (root / "configure").is_file():
            autoreconf = _which("autoreconf")
            if not autoreconf:
                raise SystemExit("zfr build: configure missing and autoreconf not in PATH")
            _run([autoreconf, "-fi"], cwd=root, dry_run=dry_run)
        builddir.mkdir(parents=True, exist_ok=True)
        if not (builddir / "Makefile").is_file():
            configure = root / "configure"
            _run([str(configure), f"--prefix={root / 'stage'}"], cwd=builddir, dry_run=dry_run)
        make = _which("make") or "make"
        cmd = [make, "-C", str(builddir)]
        if verbose:
            cmd.append("V=1")
        _run(cmd, cwd=root, dry_run=dry_run)
        return sysinfo

    if name == "cargo":
        cargo = _which("cargo")
        if not cargo:
            raise SystemExit("zfr build: cargo not found in PATH")
        cmd = [cargo, "build", "--release"]
        if verbose:
            cmd.append("-v")
        _run(cmd, cwd=root, dry_run=dry_run)
        return sysinfo

    if name == "go":
        go = _which("go")
        if not go:
            raise SystemExit("zfr build: go not found in PATH")
        _run([go, "build", "./..."], cwd=root, dry_run=dry_run)
        return sysinfo

    if name == "npm":
        runner = _which("pnpm", "npm", "yarn")
        if not runner:
            raise SystemExit("zfr build: pnpm/npm/yarn not found in PATH")
        base = Path(runner).name
        if base == "pnpm":
            _run([runner, "run", "build"], cwd=root, dry_run=dry_run)
        elif base == "yarn":
            _run([runner, "build"], cwd=root, dry_run=dry_run)
        else:
            _run([runner, "run", "build"], cwd=root, dry_run=dry_run)
        return sysinfo

    if name == "make":
        make = _which("make") or "make"
        cmd = [make]
        if verbose:
            cmd.append("V=1")
        _run(cmd, cwd=root, dry_run=dry_run)
        return sysinfo

    raise SystemExit(f"zfr build: unsupported build system {name!r}")
