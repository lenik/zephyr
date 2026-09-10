# SPDX-License-Identifier: AGPL-3.0-or-later
"""Persist / load the last ``zfr package`` run for ``zfr lasterror``."""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PackagerRecord:
    name: str
    ok: bool
    summary: str
    fdm: str = ""
    error: str = ""


@dataclass
class PackageLastRun:
    root: str
    started: float
    finished: float
    jobs: int
    records: list[PackagerRecord] = field(default_factory=list)

    def failures(self) -> list[PackagerRecord]:
        return [r for r in self.records if not r.ok]


def cache_path(*, home: Path | None = None) -> Path:
    home = home if home is not None else Path.home()
    xdg = os.environ.get("XDG_CACHE_HOME", "").strip()
    base = Path(xdg) if xdg else home / ".cache"
    return base / "zfr" / "last-package.json"


def last_package_dir(*, home: Path | None = None) -> Path:
    return cache_path(home=home).parent / "last-package.d"


def prepare_last_package_dir(*, home: Path | None = None) -> Path:
    dest = last_package_dir(home=home)
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("*.fdm"):
        try:
            old.unlink()
        except OSError:
            pass
    return dest


def record_fdm_path(rec: PackagerRecord, *, home: Path | None = None) -> Path | None:
    if not rec.fdm:
        return None
    p = Path(rec.fdm)
    if p.is_file():
        return p
    cand = last_package_dir(home=home) / rec.fdm
    if cand.is_file():
        return cand
    return None


def save_last_run(run: PackageLastRun, *, path: Path | None = None) -> Path:
    dest = path or cache_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    fdm_dir = dest.parent / "last-package.d"
    fdm_dir.mkdir(parents=True, exist_ok=True)
    stored: list[dict[str, object]] = []
    for rec in run.records:
        fdm_name = ""
        src: Path | None = None
        if rec.fdm:
            p = Path(rec.fdm)
            src = p if p.is_file() else fdm_dir / p.name
            if not src.is_file():
                src = None
        if src is not None:
            fdm_name = f"{rec.name}.fdm"
            target = fdm_dir / fdm_name
            if src.resolve() != target.resolve():
                shutil.copy2(src, target)
        rec.fdm = fdm_name
        stored.append(
            {
                "name": rec.name,
                "ok": rec.ok,
                "summary": rec.summary,
                "fdm": rec.fdm,
                "error": rec.error,
            }
        )
    payload = {
        "root": run.root,
        "started": run.started,
        "finished": run.finished,
        "jobs": run.jobs,
        "records": stored,
    }
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dest


def load_last_run(*, path: Path | None = None) -> PackageLastRun | None:
    src = path or cache_path()
    if not src.is_file():
        return None
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    records = [
        PackagerRecord(
            name=str(r.get("name", "")),
            ok=bool(r.get("ok")),
            summary=str(r.get("summary", "")),
            fdm=str(r.get("fdm", "")),
            error=str(r.get("error", "")),
        )
        for r in data.get("records") or []
        if r.get("name")
    ]
    return PackageLastRun(
        root=str(data.get("root", "")),
        started=float(data.get("started") or 0),
        finished=float(data.get("finished") or time.time()),
        jobs=int(data.get("jobs") or 0),
        records=records,
    )
