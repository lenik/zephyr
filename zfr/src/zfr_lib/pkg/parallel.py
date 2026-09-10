# SPDX-License-Identifier: AGPL-3.0-or-later
"""Parallel packaging orchestration over :class:`~.provider.Packager` providers."""

from __future__ import annotations

import concurrent.futures
import subprocess
import sys
import threading
import time
from pathlib import Path

from ..fdm import FdmCapture, log_line, require_fdm_tool, reset_capture, set_capture
from ..jobs import resolve_jobs
from ..pkg_last import (
    PackageLastRun,
    PackagerRecord,
    prepare_last_package_dir,
    save_last_run,
)
from ..pkg_ui import PackagerState, StatusBoard, interactive_lasterror, print_run_summary
from .kinds import PackagingKind, detect_packaging_kinds
from .provider import PackagerContext
from .registry import packager_for
from .upload import upload_artifacts


def _plan_kinds(
    kinds: list[PackagingKind],
    *,
    no_deb: bool,
    no_rpm: bool,
) -> list[PackagingKind]:
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


def _probe_skips(
    planned: list[PackagingKind],
    ctx: PackagerContext,
) -> tuple[list[PackagingKind], list[PackagerRecord]]:
    """Split *planned* into runnable kinds vs pre-skipped records.

    Skipped packagers are excluded before worker/job sizing so they do not
    dilute ``jobs // N``.
    """
    active: list[PackagingKind] = []
    skipped: list[PackagerRecord] = []
    for kind in planned:
        packager = packager_for(kind)
        reason = packager.skip_reason(ctx)
        if reason is None:
            active.append(kind)
            continue
        log_line(f"zfr package: skipping {kind.name} ({reason})")
        skipped.append(
            PackagerRecord(
                name=kind.name,
                ok=True,
                summary="skipped",
                fdm="",
                error="",
            )
        )
    return active, skipped


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
    """Detect kinds, run packager providers in parallel, optionally upload."""
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

    def _ctx(inner_jobs: int, *, is_dry: bool) -> PackagerContext:
        return PackagerContext(
            root=root,
            jobs=inner_jobs,
            dry_run=is_dry,
            dpkg_buildopts=list(dpkg_buildopts or []),
            docker=docker,
            docker_server=docker_server,
            base_image=base_image,
        )

    probe_ctx = _ctx(jobs, is_dry=dry_run)
    active, skipped_records = _probe_skips(planned, probe_ctx)
    if not active and not dry_run:
        # All skipped: still persist a run summary.
        finished = time.time()
        run = PackageLastRun(
            root=str(root),
            started=finished,
            finished=finished,
            jobs=jobs,
            records=skipped_records,
        )
        save_last_run(run)
        print_run_summary(run)
        log_line("zfr package: nothing to package (all kinds skipped)")
        if upload:
            log_line("zfr package: upload skipped (nothing built)")
        else:
            log_line("zfr package: upload skipped (--no-upload)")
        return []

    log_line(
        "zfr package: detected "
        + ", ".join(f"{k.name}({k.path})" for k in planned)
        + (
            f"; active={len(active)} skipped={len(skipped_records)}"
            if skipped_records
            else f"; active={len(active)}"
        )
        + f"; parallel packagers≤{jobs}"
    )

    if dry_run:
        built: list[PackagingKind] = []
        n = max(1, len(active))
        workers = max(1, min(jobs, n))
        inner_jobs = max(1, jobs // workers)
        ctx = _ctx(inner_jobs, is_dry=True)
        for kind in active:
            if packager_for(kind).build(ctx):
                built.append(kind)
        if upload:
            upload_artifacts(root, built, dput_host=dput_host, dry_run=True)
        else:
            log_line("zfr package: upload skipped (--no-upload)")
        return built

    n = len(active)
    workers = max(1, min(jobs, n))
    inner_jobs = max(1, jobs // workers)
    require_fdm_tool("fdmux")
    fdm_dir = prepare_last_package_dir()

    board = StatusBoard(
        title="Packaging...",
        states=[PackagerState(name=k.name) for k in active]
        + [PackagerState(name=r.name) for r in skipped_records],
        enabled=sys.stdout.isatty(),
    )
    board.start()
    for rec in skipped_records:
        board.set_ok(rec.name, "skipped")

    records: list[PackagerRecord] = list(skipped_records)
    built_map: dict[str, PackagingKind] = {}
    started = time.time()
    lock = threading.Lock()

    def _worker(kind: PackagingKind) -> PackagerRecord:
        fdm_path = fdm_dir / f"{kind.name}.fdm"
        fdm_path.write_bytes(b"")
        cap = FdmCapture(fdm_path)
        token = set_capture(cap)
        board.set_running(kind.name)
        done = threading.Event()

        def _poll() -> None:
            while not done.wait(0.15):
                tip = cap.last_line()
                if tip:
                    board.set_tip(kind.name, tip)

        threading.Thread(target=_poll, daemon=True).start()
        err = ""
        summary = "packaged"
        ok = False
        try:
            did = packager_for(kind).build(_ctx(inner_jobs, is_dry=False))
            ok = True
            summary = "packaged" if did else "skipped"
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
        except Exception as exc:  # noqa: BLE001
            ok = False
            err = str(exc) or exc.__class__.__name__
            board.set_fail(kind.name, err)
            summary = f"error: {err}"
        finally:
            done.set()
            reset_capture(token)

        record = PackagerRecord(
            name=kind.name,
            ok=ok,
            summary=summary,
            fdm=str(fdm_path),
            error=err,
        )
        with lock:
            records.append(record)
            if ok and summary == "packaged":
                built_map[kind.name] = kind
        return record

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_worker, k) for k in active]
        concurrent.futures.wait(futs)
        for f in futs:
            f.result()

    board.finish()
    finished = time.time()
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

    built = [built_map[k.name] for k in active if k.name in built_map]
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
