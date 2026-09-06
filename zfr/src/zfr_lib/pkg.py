# SPDX-License-Identifier: AGPL-3.0-or-later
"""Detect packaging types (deb, rpm, npm, …) and build packages."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .packaging_host import can_build_local, find_build_host_file


@dataclass(frozen=True)
class PackagingKind:
    name: str
    """deb, rpm, npm, vsix, mingw, innosetup, wix, macos, arch, freebsd."""
    path: str = ""


_DPUT_ATTEMPTS = 3
_DPUT_RETRY_DELAY_S = 1.0

# Optional packaging/ Makefile targets (beyond debian/ and npm).
_MAKE_TARGETS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("rpm", "packaging/rpm", ("rpm", "srpm")),
    ("mingw", "packaging/win32/mingw", ("local",)),
    ("innosetup", "packaging/win32/innosetup", ("local",)),
    ("wix", "packaging/win32/wix", ("local",)),
    ("macos", "packaging/macos", ("local",)),
    ("arch", "packaging/arch", ("local",)),
    ("freebsd", "packaging/freebsd", ("local",)),
)


def resolve_rpm_dir(root: Path) -> Path | None:
    for rel in ("packaging/rpm", "rpm"):
        d = root / rel
        if (d / "Makefile").is_file():
            return d
    return None


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
    for kind, rel, _goals in _MAKE_TARGETS:
        if kind == "rpm":
            d = resolve_rpm_dir(root)
            if d is not None:
                found.append(PackagingKind("rpm", str(d.relative_to(root))))
            continue
        d = root / rel
        if (d / "Makefile").is_file():
            found.append(PackagingKind(kind, rel))
    return found


def _run(cmd: list[str], *, cwd: Path | None = None, dry_run: bool = False) -> None:
    print("+", " ".join(cmd), flush=True)
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def _dput_with_retries(host: str, changes_file: str, *, dry_run: bool = False) -> None:
    cmd = ["dput", "-f", host, changes_file]
    if dry_run:
        print("+", " ".join(cmd), flush=True)
        return
    last: subprocess.CalledProcessError | None = None
    for attempt in range(1, _DPUT_ATTEMPTS + 1):
        print("+", " ".join(cmd), flush=True)
        try:
            subprocess.run(cmd, check=True)
            return
        except subprocess.CalledProcessError as exc:
            last = exc
            if attempt >= _DPUT_ATTEMPTS:
                break
            print(
                f"dput failed (attempt {attempt}/{_DPUT_ATTEMPTS}); "
                f"retrying in {_DPUT_RETRY_DELAY_S:g}s…",
                flush=True,
            )
            time.sleep(_DPUT_RETRY_DELAY_S)
    assert last is not None
    raise last


def _load_dput_host_default() -> str:
    for base in (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")),
        Path.home() / ".config",
    ):
        path = base / "gh-makerelease.options"
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.split("#", 1)[0].strip()
            if line.startswith("-p") or line.startswith("--dput-host"):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    return parts[1].strip()
                # form: -pHOST
                if line.startswith("-p") and len(line) > 2 and not line.startswith("-p "):
                    return line[2:]
    return ""


def _find_changes(root: Path, version: str) -> Path | None:
    parent = root.parent
    hits = sorted(parent.glob(f"*_{version}_*.changes")) + sorted(
        parent.glob(f"*_{version}.changes")
    )
    return hits[0] if hits else None


def _project_version(root: Path) -> str:
    for path in (root / "VERSION", root / "debian" / "changelog"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if path.name == "VERSION":
            return text.strip().splitlines()[0].strip().lstrip("v")
        # changelog: zephyr (2.8.12) ...
        import re

        m = re.search(r"^\S+\s+\(([^)]+)\)", text, re.M)
        if m:
            return m.group(1).split(":")[-1]
    return ""


def package_deb(
    root: Path,
    *,
    dpkg_buildopts: list[str] | None = None,
    docker: bool = False,
    docker_server: str = "",
    base_image: str = "b4f-debian:trixie",
    dry_run: bool = False,
) -> None:
    opts = list(dpkg_buildopts or [])
    if docker or docker_server:
        # Prefer build4 when requested (same as gh-makerelease).
        build4 = shutil.which("build4")
        if not build4:
            raise SystemExit("zfr package: build4 not found in PATH (needed for -d/--docker)")
        cmd = [build4]
        if docker_server:
            cmd += ["-s", docker_server]
        cmd += ["-B", base_image, str(root)]
        _run(cmd, dry_run=dry_run)
        return
    if shutil.which("debuild"):
        _run(["debuild", *opts], cwd=root, dry_run=dry_run)
    else:
        _run(["dpkg-buildpackage", *opts], cwd=root, dry_run=dry_run)


def package_npm_or_vsix(root: Path, kind: str, *, dry_run: bool = False) -> None:
    runner = shutil.which("pnpm") or shutil.which("npm")
    if not runner:
        raise SystemExit("zfr package: pnpm/npm not found in PATH")
    print(f"zfr package: building {kind}", flush=True)
    if Path(runner).name == "pnpm":
        _run([runner, "package"], cwd=root, dry_run=dry_run)
    else:
        _run([runner, "run", "package"], cwd=root, dry_run=dry_run)


def package_make_target(
    root: Path,
    kind: str,
    rel: str,
    goals: tuple[str, ...],
    *,
    dry_run: bool = False,
) -> bool:
    """Build one packaging/ Makefile target. Return False if skipped."""
    if kind == "rpm":
        pkgdir = resolve_rpm_dir(root)
    else:
        pkgdir = root / rel
        if not (pkgdir / "Makefile").is_file():
            pkgdir = None
    if pkgdir is None:
        return False

    if can_build_local(kind) or os.environ.get("ZEPHYR_FORCE_LOCAL") == "1":
        mode = "local"
    elif find_build_host_file(root, kind) is not None:
        # Makefiles that use host.sh will skip/remote themselves; still invoke make.
        mode = "make"
    else:
        print(
            f"zfr package: skipping {kind} (no local tools and no .build-host)",
            flush=True,
        )
        return False

    print(f"zfr package: building {kind} ({mode})", flush=True)
    env = os.environ.copy()
    env["ZEPHYR_SRCDIR"] = str(root)
    if mode == "local":
        env["ZEPHYR_FORCE_LOCAL"] = "1"
    cmd = ["make", "-C", str(pkgdir), *goals]
    print("+", " ".join(cmd), flush=True)
    if dry_run:
        return True
    subprocess.run(cmd, cwd=root, env=env, check=True)
    return True


def upload_artifacts(
    root: Path,
    kinds: list[PackagingKind],
    *,
    dput_host: str = "",
    dry_run: bool = False,
) -> None:
    """Upload built packages (dput for deb; npm publish for npm/vsix when configured)."""
    names = {k.name for k in kinds}
    if "deb" in names:
        host = dput_host or _load_dput_host_default()
        if not host:
            print("zfr package: upload skipped (no dput host; pass -p/--dput-host)", flush=True)
        else:
            ver = _project_version(root)
            changes = _find_changes(root, ver) if ver else None
            if changes is None:
                # Fallback: newest changes next to project
                candidates = sorted(root.parent.glob("*.changes"), key=lambda p: p.stat().st_mtime)
                changes = candidates[-1] if candidates else None
            if changes is None:
                raise SystemExit("zfr package: no .changes file found for dput upload")
            print(f"zfr package: uploading {changes.name} → {host}", flush=True)
            _dput_with_retries(host, str(changes), dry_run=dry_run)

    if names & {"npm", "vsix"}:
        # Marketplace / npm registry publish is intentionally opt-in via env.
        if os.environ.get("ZFR_NPM_PUBLISH", "").strip() in {"1", "true", "yes"}:
            runner = shutil.which("pnpm") or shutil.which("npm")
            if runner:
                _run([runner, "publish"], cwd=root, dry_run=dry_run)
        else:
            print(
                "zfr package: npm/vsix registry publish skipped "
                "(set ZFR_NPM_PUBLISH=1 to enable)",
                flush=True,
            )


def package_project(
    root: Path,
    *,
    upload: bool = True,
    dput_host: str = "",
    no_deb: bool = False,
    no_rpm: bool = False,
    only: list[str] | None = None,
    dpkg_buildopts: list[str] | None = None,
    docker: bool = False,
    docker_server: str = "",
    base_image: str = "b4f-debian:trixie",
    dry_run: bool = False,
) -> list[PackagingKind]:
    """Detect and build packages; optionally upload. Returns kinds that were built."""
    root = root.resolve()
    kinds = detect_packaging_kinds(root)
    if only:
        want = {x.strip().lower() for x in only if x.strip()}
        kinds = [k for k in kinds if k.name in want]
    if not kinds:
        raise SystemExit(f"zfr package: no packaging types detected under {root}")

    print(
        "zfr package: detected " + ", ".join(f"{k.name}({k.path})" for k in kinds),
        flush=True,
    )

    built: list[PackagingKind] = []
    for kind in kinds:
        if kind.name == "deb":
            if no_deb:
                print("zfr package: skipping deb (--no-deb)", flush=True)
                continue
            package_deb(
                root,
                dpkg_buildopts=dpkg_buildopts,
                docker=docker,
                docker_server=docker_server,
                base_image=base_image,
                dry_run=dry_run,
            )
            built.append(kind)
            continue
        if kind.name in {"npm", "vsix"}:
            package_npm_or_vsix(root, kind.name, dry_run=dry_run)
            built.append(kind)
            continue
        if kind.name == "rpm" and no_rpm:
            print("zfr package: skipping rpm (--no-rpm)", flush=True)
            continue
        goals = next(g for n, _r, g in _MAKE_TARGETS if n == kind.name)
        rel = kind.path or next(r for n, r, _g in _MAKE_TARGETS if n == kind.name)
        if package_make_target(root, kind.name, rel, goals, dry_run=dry_run):
            built.append(kind)

    if upload:
        upload_artifacts(root, built, dput_host=dput_host, dry_run=dry_run)
    else:
        print("zfr package: upload skipped (--no-upload)", flush=True)
    return built
