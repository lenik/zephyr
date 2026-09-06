# SPDX-License-Identifier: AGPL-3.0-or-later
"""Makefile-based packager (rpm, mingw, innosetup, …)."""

from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path

from ..cmd_run import merge_env, run_cmd
from ..jobs import resolve_jobs
from ..packaging import rpm_topdir
from ..packaging_host import can_build_local, find_build_host_file, remote_build
from ..stream_mark import log_line
from .kinds import resolve_rpm_dir, target_meta
from .provider import PackagerContext


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


class MakeTargetPackager:
    """Build one ``packaging/<kind>`` Makefile target locally or via .build-host."""

    def __init__(self, kind: str, rel: str = "") -> None:
        self._kind = kind
        self._rel = rel

    @property
    def name(self) -> str:
        return self._kind

    def _pkgdir(self, ctx: PackagerContext) -> Path | None:
        kind = self._kind
        if kind == "rpm":
            return resolve_rpm_dir(ctx.root)
        default_rel, _goals, _outs = target_meta(kind)
        rel = self._rel or default_rel
        pkgdir = ctx.root / rel
        if not (pkgdir / "Makefile").is_file():
            return None
        return pkgdir

    def skip_reason(self, ctx: PackagerContext) -> str | None:
        """Skip when Makefile is missing or neither local nor remote build works."""
        if self._pkgdir(ctx) is None:
            return "no packaging Makefile"
        force_local = os.environ.get("ZEPHYR_FORCE_LOCAL") == "1"
        if can_build_local(self._kind) or force_local:
            return None
        if find_build_host_file(ctx.root, self._kind) is not None:
            return None
        return "no local tools and no .build-host"

    def build(self, ctx: PackagerContext) -> bool:
        jobs = resolve_jobs(ctx.jobs)
        kind = self._kind
        pkgdir = self._pkgdir(ctx)
        if pkgdir is None:
            return False

        reason = self.skip_reason(ctx)
        if reason is not None:
            log_line(f"zfr package: skipping {kind} ({reason})")
            return False

        force_local = os.environ.get("ZEPHYR_FORCE_LOCAL") == "1"
        if can_build_local(kind) or force_local:
            mode = "local"
        else:
            mode = "remote"

        _rel, goals, out_rels = target_meta(kind)
        log_line(f"zfr package: building {kind} ({mode}, jobs={jobs})")
        if ctx.dry_run:
            if mode == "local":
                log_line("+ " + " ".join(["make", f"-j{jobs}", "-C", str(pkgdir), *goals]))
            else:
                log_line(f"+ remote_build {kind} make -j{jobs} -C …")
            return True

        if mode == "local":
            env = merge_env(
                {
                    "ZEPHYR_SRCDIR": str(ctx.root),
                    "ZEPHYR_FORCE_LOCAL": "1",
                }
            )
            run_cmd(
                ["make", f"-j{jobs}", "-C", str(pkgdir), *goals],
                cwd=ctx.root,
                env=env,
            )
            return True

        pkg_rel = pkgdir.relative_to(ctx.root).as_posix()
        if kind == "rpm":
            out_rel = f"{pkg_rel}/out"
            goals_s = " ".join(goals)
            cmd = [
                f"!make -j{jobs} -C {shlex.quote(pkg_rel)} "
                f'TOPDIR="$ZEPHYR_SRCDIR/{out_rel}" {goals_s}'
            ]
            remote_build(ctx.root, kind, local_cmd=cmd, out_rels=(out_rel,))
            _merge_rpmbuild_into_topdir(ctx.root / out_rel)
        else:
            remote_build(
                ctx.root,
                kind,
                local_cmd=["make", f"-j{jobs}", "-C", pkg_rel, *goals],
                out_rels=out_rels or (f"{pkg_rel}/out",),
            )
        return True


def package_make_target(
    root: Path,
    kind: str,
    rel: str,
    goals: tuple[str, ...],
    *,
    jobs: int = 0,
    dry_run: bool = False,
) -> bool:
    """Backward-compatible wrapper; *goals* is taken from :func:`target_meta`."""
    del goals  # registry is authoritative
    return MakeTargetPackager(kind, rel).build(
        PackagerContext(root=Path(root), jobs=jobs, dry_run=dry_run)
    )
