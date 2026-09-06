# SPDX-License-Identifier: AGPL-3.0-or-later
"""Persist / load the last ``zfr package`` run for ``zfr lasterror``."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class PackagerRecord:
    name: str
    ok: bool
    summary: str
    marked: str = ""
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


def save_last_run(run: PackageLastRun, *, path: Path | None = None) -> Path:
    dest = path or cache_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "root": run.root,
        "started": run.started,
        "finished": run.finished,
        "jobs": run.jobs,
        "records": [asdict(r) for r in run.records],
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
            marked=str(r.get("marked", "")),
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
