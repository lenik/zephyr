# SPDX-License-Identifier: AGPL-3.0-or-later
"""Upload built packages (dput / optional npm publish)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from ..cmd_run import run_cmd
from ..stream_mark import log_line
from .kinds import PackagingKind

_DPUT_ATTEMPTS = 3
_DPUT_RETRY_DELAY_S = 1.0


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
        for name in ("zfr-release.options", "gh-makerelease.options"):
            path = base / name
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
                    if "=" in line:
                        return line.split("=", 1)[1].strip()
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


def upload_artifacts(
    root: Path,
    kinds: list[PackagingKind],
    *,
    dput_host: str = "",
    dry_run: bool = False,
) -> None:
    """Upload built packages (dput for deb; npm publish when configured)."""
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
                run_cmd([runner, "publish"], cwd=root, dry_run=dry_run)
        else:
            log_line(
                "zfr package: npm/vsix registry publish skipped "
                "(set ZFR_NPM_PUBLISH=1 to enable)"
            )
