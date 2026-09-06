# SPDX-License-Identifier: AGPL-3.0-or-later
"""Detect packaging types (deb, rpm, npm, …) and build packages.

Logic extracted from gh-makerelease's build / packaging stages.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .cmd_run import merge_env, run_cmd
from .jobs import resolve_jobs
from .packaging import rpm_topdir
from .packaging_host import can_build_local, find_build_host_file, remote_build
from .pkg_docker import build4_debian, build4_debian_remote
from .pkg_last import PackageLastRun, PackagerRecord, save_last_run
from .pkg_ui import StatusBoard, interactive_lasterror, print_run_summary
from .stream_mark import StreamRecorder, log_line, reset_recorder, set_recorder


@dataclass(frozen=True)
class PackagingKind:
    name: str
    """deb, rpm, npm, vsix, mingw, innosetup, wix, macos, arch, freebsd."""
    path: str = ""


_DPUT_ATTEMPTS = 3
_DPUT_RETRY_DELAY_S = 1.0

# Optional packaging/ Makefile targets (beyond debian/ and npm).
# (kind, rel_dir, make_goals, out_rels for remote fetch)
_MAKE_TARGETS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("rpm", "packaging/rpm", ("rpm", "srpm"), ()),
    ("mingw", "packaging/win32/mingw", ("local",), ("packaging/win32/mingw/out",)),
    ("innosetup", "packaging/win32/innosetup", ("local",), ("packaging/win32/innosetup/out",)),
    ("wix", "packaging/win32/wix", ("local",), ("packaging/win32/wix/out",)),
    ("macos", "packaging/macos", ("local",), ("packaging/macos/out",)),
    ("arch", "packaging/arch", ("local",), ("packaging/arch/out",)),
    ("freebsd", "packaging/freebsd", ("local",), ("packaging/freebsd/out",)),
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
    for kind, rel, _goals, _outs in _MAKE_TARGETS:
        if kind == "rpm":
            d = resolve_rpm_dir(root)
            if d is not None:
                found.append(PackagingKind("rpm", str(d.relative_to(root))))
            continue
        d = root / rel
        if (d / "Makefile").is_file():
            found.append(PackagingKind(kind, rel))
    return found


def _run(cmd: list[str], *, cwd: Path | None = None, dry_run: bool = False, env: dict[str, str] | None = None) -> None:
    run_cmd(cmd, cwd=cwd, dry_run=dry_run, env=env)


def _dput_with_retries(host: str, changes_file: str, *, dry_run: bool = False) -> None:
    cmd = ["dput", "-f", host, changes_file]
    if dry_run:
        log_line("+ " + " ".join(cmd))
        return
    last: subprocess.CalledProcessError | None = None
    for attempt in range(1, _DPUT_ATTEMPTS + 1):
        try:
            run_cmd(cmd, dry_run=False)
            return
        except subprocess.CalledProcessError as exc:
            last = exc
            if attempt >= _DPUT_ATTEMPTS:
                break
            log_line(
                f"dput failed (attempt {attempt}/{_DPUT_ATTEMPTS}); "
                f"retrying in {_DPUT_RETRY_DELAY_S:g}s…"
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
    jobs: int = 0,
    dry_run: bool = False,
) -> None:
    opts = list(dpkg_buildopts or [])
    jobs = resolve_jobs(jobs)
    if docker or docker_server:
        if docker_server:
            build4_debian_remote(
                root,
                docker_server=docker_server,
                base_image=base_image,
                dpkg_buildopts=opts,
                jobs=jobs,
                dry_run=dry_run,
            )
        else:
            build4_debian(
                root,
                base_image=base_image,
                dpkg_buildopts=opts,
                jobs=jobs,
                dry_run=dry_run,
            )
        return
    env = merge_env()
    prev = env.get("DEB_BUILD_OPTIONS", "").strip()
    parallel = f"parallel={jobs}"
    env["DEB_BUILD_OPTIONS"] = f"{prev} {parallel}".strip() if prev else parallel
    if shutil.which("debuild"):
        cmd = ["debuild", f"-j{jobs}", *opts]
    else:
        cmd = ["dpkg-buildpackage", f"-j{jobs}", *opts]
    run_cmd(cmd, cwd=root, env=env, dry_run=dry_run)


def package_npm_or_vsix(root: Path, kind: str, *, dry_run: bool = False) -> None:
    runner = shutil.which("pnpm") or shutil.which("npm")
    if not runner:
        raise SystemExit("zfr package: pnpm/npm not found in PATH")
    log_line(f"zfr package: building {kind}")
    if Path(runner).name == "pnpm":
        run_cmd([runner, "package"], cwd=root, dry_run=dry_run)
    else:
        run_cmd([runner, "run", "package"], cwd=root, dry_run=dry_run)


def _merge_rpmbuild_into_topdir(src: Path) -> None:
    """Add files from *src* into ``%_topdir`` without overwriting or deleting."""
    if not src.is_dir():
        return
    top = rpm_topdir()
    added = 0
    skipped = 0
    for sub in ("RPMS", "SRPMS", "SOURCES", "SPECS"):
        src_sub = src / sub
        if not src_sub.exists():
            continue
        dest_sub = top / sub
        dest_sub.mkdir(parents=True, exist_ok=True)
        if not src_sub.is_dir():
            continue
        for item in src_sub.rglob("*"):
            if not item.is_file():
                continue
            rel = item.relative_to(src_sub)
            dest = dest_sub / rel
            if dest.exists():
                skipped += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            added += 1
    if added or skipped:
        log_line(
            f"zfr package: merged RPM artifacts into {top} "
            f"(added={added}, skipped_existing={skipped})"
        )


def _target_meta(kind: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    for name, rel, goals, outs in _MAKE_TARGETS:
        if name == kind:
            return rel, goals, outs
    raise KeyError(kind)


def package_make_target(
    root: Path,
    kind: str,
    rel: str,
    goals: tuple[str, ...],
    *,
    jobs: int = 0,
    dry_run: bool = False,
) -> bool:
    """Build one packaging/ Makefile target locally or via .build-host. Return False if skipped."""
    jobs = resolve_jobs(jobs)
    if kind == "rpm":
        pkgdir = resolve_rpm_dir(root)
    else:
        pkgdir = root / rel
        if not (pkgdir / "Makefile").is_file():
            pkgdir = None
    if pkgdir is None:
        return False

    force_local = os.environ.get("ZEPHYR_FORCE_LOCAL") == "1"
    if can_build_local(kind) or force_local:
        mode = "local"
    elif find_build_host_file(root, kind) is not None:
        mode = "remote"
    else:
        log_line(f"zfr package: skipping {kind} (no local tools and no .build-host)")
        return False

    log_line(f"zfr package: building {kind} ({mode}, jobs={jobs})")
    if dry_run:
        if mode == "local":
            log_line("+ " + " ".join(["make", f"-j{jobs}", "-C", str(pkgdir), *goals]))
        else:
            log_line(f"+ remote_build {kind} make -j{jobs} -C …")
        return True

    if mode == "local":
        env = merge_env(
            {
                "ZEPHYR_SRCDIR": str(root),
                "ZEPHYR_FORCE_LOCAL": "1",
            }
        )
        cmd = ["make", f"-j{jobs}", "-C", str(pkgdir), *goals]
        run_cmd(cmd, cwd=root, env=env)
        return True

    # remote
    pkg_rel = pkgdir.relative_to(root).as_posix()
    _, _goals, out_rels = _target_meta(kind)
    if kind == "rpm":
        out_rel = f"{pkg_rel}/out"
        goals_s = " ".join(goals)
        cmd = [
            f"!make -j{jobs} -C {shlex.quote(pkg_rel)} "
            f'TOPDIR="$ZEPHYR_SRCDIR/{out_rel}" {goals_s}'
        ]
        remote_build(root, kind, local_cmd=cmd, out_rels=(out_rel,))
        _merge_rpmbuild_into_topdir(root / out_rel)
    else:
        remote_build(
            root,
            kind,
            local_cmd=["make", f"-j{jobs}", "-C", pkg_rel, *goals],
            out_rels=out_rels or (f"{pkg_rel}/out",),
        )
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
            log_line("zfr package: upload skipped (no dput host; pass -p/--dput-host)")
        else:
            ver = _project_version(root)
            changes = _find_changes(root, ver) if ver else None
            if changes is None:
                candidates = sorted(root.parent.glob("*.changes"), key=lambda p: p.stat().st_mtime)
                changes = candidates[-1] if candidates else None
            if changes is None:
                raise SystemExit("zfr package: no .changes file found for dput upload")
            log_line(f"zfr package: uploading {changes.name} → {host}")
            _dput_with_retries(host, str(changes), dry_run=dry_run)

    if names & {"npm", "vsix"}:
        if os.environ.get("ZFR_NPM_PUBLISH", "").strip() in {"1", "true", "yes"}:
            runner = shutil.which("pnpm") or shutil.which("npm")
            if runner:
                _run([runner, "publish"], cwd=root, dry_run=dry_run)
        else:
            log_line(
                "zfr package: npm/vsix registry publish skipped "
                "(set ZFR_NPM_PUBLISH=1 to enable)"
            )


def _plan_kinds(
    kinds: list[PackagingKind],
    *,
    no_deb: bool,
    no_rpm: bool,
) -> list[PackagingKind]:
    """Filter kinds that will actually run (skip flags applied)."""
    planned: list[PackagingKind] = []
    for kind in kinds:
        if kind.name == "deb" and no_deb:
            log_line("zfr package: skipping deb (--no-deb)")
            continue
        if kind.name == "rpm" and no_rpm:
            log_line("zfr package: skipping rpm (--no-rpm)")
            continue
        planned.append(kind)
    return planned


def _run_one_kind(
    root: Path,
    kind: PackagingKind,
    *,
    dpkg_buildopts: list[str] | None,
    docker: bool,
    docker_server: str,
    base_image: str,
    dry_run: bool,
    inner_jobs: int,
) -> tuple[bool, str]:
    """Execute one packager. Returns (ok_or_skipped_as_built, error_message).

    Raises on hard failure after recording. Returns (False, '') if skipped without build.
    """
    if kind.name == "deb":
        package_deb(
            root,
            dpkg_buildopts=dpkg_buildopts,
            docker=docker,
            docker_server=docker_server,
            base_image=base_image,
            jobs=inner_jobs,
            dry_run=dry_run,
        )
        return True, ""
    if kind.name in {"npm", "vsix"}:
        package_npm_or_vsix(root, kind.name, dry_run=dry_run)
        return True, ""
    _rel, goals, _outs = _target_meta(kind.name)
    rel = kind.path or _rel
    built = package_make_target(
        root, kind.name, rel, goals, jobs=inner_jobs, dry_run=dry_run
    )
    return built, ""


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
    jobs: int = 0,
    interactive_errors: bool = True,
) -> list[PackagingKind]:
    """Detect and build packages in parallel; optionally upload.

    *jobs* is the max number of concurrent packagers (deb/rpm/…). Each
    packager still receives an inner parallel count for make/debuild.
    """
    import concurrent.futures
    import sys
    import time as time_mod

    from .pkg_ui import PackagerState

    root = root.resolve()
    jobs = resolve_jobs(jobs)
    kinds = detect_packaging_kinds(root)
    if only:
        want = {x.strip().lower() for x in only if x.strip()}
        kinds = [k for k in kinds if k.name in want]
    if not kinds:
        raise SystemExit(f"zfr package: no packaging types detected under {root}")

    planned = _plan_kinds(kinds, no_deb=no_deb, no_rpm=no_rpm)
    if not planned:
        raise SystemExit("zfr package: nothing to package after --no-deb/--no-rpm filters")

    log_line(
        "zfr package: detected "
        + ", ".join(f"{k.name}({k.path})" for k in planned)
        + f"; parallel packagers≤{jobs}"
    )

    if dry_run:
        built: list[PackagingKind] = []
        for kind in planned:
            ok, _err = _run_one_kind(
                root,
                kind,
                dpkg_buildopts=dpkg_buildopts,
                docker=docker,
                docker_server=docker_server,
                base_image=base_image,
                dry_run=True,
                inner_jobs=jobs,
            )
            if ok:
                built.append(kind)
        if upload:
            upload_artifacts(root, built, dput_host=dput_host, dry_run=True)
        else:
            log_line("zfr package: upload skipped (--no-upload)")
        return built

    n = len(planned)
    workers = max(1, min(jobs, n))
    # Share make/debuild parallelism across concurrent packagers.
    inner_jobs = max(1, jobs // workers)

    board = StatusBoard(
        title="Packaging...",
        states=[PackagerState(name=k.name) for k in planned],
        enabled=sys.stdout.isatty(),
    )
    board.start()

    records: list[PackagerRecord] = []
    built_map: dict[str, PackagingKind] = {}
    started = time_mod.time()
    lock = __import__("threading").Lock()

    def _worker(kind: PackagingKind) -> PackagerRecord:
        rec = StreamRecorder()
        token = set_recorder(rec)
        board.set_running(kind.name)
        done = __import__("threading").Event()

        def _poll() -> None:
            while not done.wait(0.15):
                tip = rec.last_line()
                if tip:
                    board.set_tip(kind.name, tip)

        poller = __import__("threading").Thread(target=_poll, daemon=True)
        poller.start()
        err = ""
        summary = "packaged"
        ok = False
        try:
            did, _ = _run_one_kind(
                root,
                kind,
                dpkg_buildopts=dpkg_buildopts,
                docker=docker,
                docker_server=docker_server,
                base_image=base_image,
                dry_run=False,
                inner_jobs=inner_jobs,
            )
            if did:
                ok = True
                summary = "packaged"
                board.set_ok(kind.name, summary)
            else:
                ok = True
                summary = "skipped"
                board.set_ok(kind.name, summary)
        except SystemExit as exc:
            ok = False
            err = str(exc) or "failed"
            board.set_fail(kind.name, err)
            summary = f"error: {err}"
        except subprocess.CalledProcessError as exc:
            ok = False
            err = f"exit {exc.returncode}"
            board.set_fail(kind.name, err)
            summary = f"error: {err}"
        except Exception as exc:  # noqa: BLE001 — surface any packager failure
            ok = False
            err = str(exc) or exc.__class__.__name__
            board.set_fail(kind.name, err)
            summary = f"error: {err}"
        finally:
            done.set()
            reset_recorder(token)

        record = PackagerRecord(
            name=kind.name,
            ok=ok,
            summary=summary,
            marked=rec.marked(),
            error=err,
        )
        with lock:
            records.append(record)
            if ok and summary == "packaged":
                built_map[kind.name] = kind
        return record

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_worker, k) for k in planned]
        concurrent.futures.wait(futs)
        # surface unexpected thread exceptions
        for f in futs:
            f.result()

    board.finish()
    finished = time_mod.time()
    # Stable order matching planned
    by_name = {r.name: r for r in records}
    ordered = [by_name[k.name] for k in planned if k.name in by_name]
    run = PackageLastRun(
        root=str(root),
        started=started,
        finished=finished,
        jobs=jobs,
        records=ordered,
    )
    save_last_run(run)

    if not board.enabled:
        print_run_summary(run)

    built = [built_map[k.name] for k in planned if k.name in built_map]
    failures = run.failures()
    if failures:
        if interactive_errors and sys.stdin.isatty() and sys.stdout.isatty():
            interactive_lasterror(run, only_failures=True)
        raise SystemExit(
            f"zfr package: {len(failures)} packager(s) failed "
            f"(revisit with `zfr lasterror`)"
        )

    if upload:
        upload_artifacts(root, built, dput_host=dput_host, dry_run=False)
    else:
        log_line("zfr package: upload skipped (--no-upload)")
    return built
