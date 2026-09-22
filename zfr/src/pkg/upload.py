# SPDX-License-Identifier: AGPL-3.0-or-later
"""Upload / publish built packages via ~/.config/zfr/scripts/ hooks.

Hooks (executable scripts; missing → warn, do not fail the build):

  upload_deb / publish_deb
  upload_rpm / publish_rpm
  upload_npm / publish_npm
  upload_vsix / publish_vsix

``upload_*`` receives artifact path(s) as argv. ``publish_*`` is called with
no arguments after a successful upload for that kind (e.g. aptly process /
createrepo rescan). Working directory is the project root.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

from cmd_run import run_cmd
from fdm import log_line
from .kinds import PackagingKind


def _config_scripts_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "zfr" / "scripts"


def _hook_path(name: str) -> Path:
    return _config_scripts_dir() / name


def _warn_missing(name: str, why: str) -> None:
    log_line(
        f"zfr package: warn: missing {_hook_path(name)} ({why}); "
        f"install an executable hook under ~/.config/zfr/scripts/"
    )


def _run_hook(name: str, args: list[str], *, cwd: Path, dry_run: bool) -> bool:
    """Run a hook script. Return True if invoked, False if missing/skipped."""
    path = _hook_path(name)
    if not path.is_file():
        return False
    mode = path.stat().st_mode
    if not (mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)):
        log_line(f"zfr package: warn: {path} is not executable; chmod +x it")
        return False
    cmd = [str(path), *args]
    if dry_run:
        log_line("+ " + " ".join(cmd))
        return True
    log_line(f"zfr package: {name} → {' '.join(args) if args else '(no args)'}")
    run_cmd(cmd, cwd=cwd, dry_run=False)
    return True


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


def _find_rpms(root: Path) -> list[Path]:
    name = root.name
    hits: list[Path] = []
    search_roots = [root, root.parent]
    rpm_home = Path.home() / "rpmbuild" / "RPMS"
    if rpm_home.is_dir():
        search_roots.append(rpm_home)
    for base in search_roots:
        if not base.is_dir():
            continue
        hits.extend(sorted(base.rglob(f"{name}*.rpm")))
        hits.extend(sorted(base.rglob(f"lib{name}*.rpm")))
    by_name: dict[str, Path] = {}
    for path in hits:
        if path.name.endswith(".src.rpm"):
            continue
        prev = by_name.get(path.name)
        if prev is None or path.stat().st_mtime >= prev.stat().st_mtime:
            by_name[path.name] = path
    return sorted(by_name.values(), key=lambda p: p.stat().st_mtime)


def _upload_then_publish(
    *,
    kind: str,
    artifacts: list[Path],
    root: Path,
    dry_run: bool,
) -> None:
    upload = f"upload_{kind}"
    publish = f"publish_{kind}"
    if not artifacts:
        log_line(f"zfr package: no {kind} artifacts to upload")
        return
    if not _hook_path(upload).is_file():
        _warn_missing(upload, f"built {kind} packages need uploading")
        return
    ok = _run_hook(
        upload,
        [str(p) for p in artifacts],
        cwd=root,
        dry_run=dry_run,
    )
    if not ok:
        return
    if not _hook_path(publish).is_file():
        _warn_missing(publish, f"after upload_{kind}; repo may need a rescan/process")
        return
    _run_hook(publish, [], cwd=root, dry_run=dry_run)


def upload_artifacts(
    root: Path,
    kinds: list[PackagingKind],
    *,
    dput_host: str = "",
    dry_run: bool = False,
) -> None:
    """Dispatch to ~/.config/zfr/scripts/ upload_* / publish_* hooks.

    *dput_host* is accepted for CLI compatibility but ignored; configure
    ``upload_deb`` (e.g. ``dput -f s1``) instead.
    """
    if dput_host:
        log_line(
            "zfr package: note: --dput-host is deprecated; "
            "configure ~/.config/zfr/scripts/upload_deb instead"
        )

    names = {k.name for k in kinds}
    root = root.resolve()

    if "deb" in names:
        ver = _project_version(root)
        changes = _find_changes(root, ver) if ver else None
        if changes is None:
            candidates = sorted(
                root.parent.glob("*.changes"), key=lambda p: p.stat().st_mtime
            )
            changes = candidates[-1] if candidates else None
        if changes is None:
            log_line("zfr package: warn: no .changes file found for deb upload")
        else:
            # Pass .changes; upload_deb (dput) pulls sibling files itself.
            _upload_then_publish(
                kind="deb",
                artifacts=[changes],
                root=root,
                dry_run=dry_run,
            )

    if "rpm" in names:
        _upload_then_publish(
            kind="rpm",
            artifacts=_find_rpms(root),
            root=root,
            dry_run=dry_run,
        )

    if "npm" in names:
        # package.json directory is the artifact root.
        _upload_then_publish(
            kind="npm",
            artifacts=[root],
            root=root,
            dry_run=dry_run,
        )

    if "vsix" in names:
        vsix = sorted(root.glob("*.vsix"), key=lambda p: p.stat().st_mtime)
        if not vsix:
            vsix = sorted(root.rglob("*.vsix"), key=lambda p: p.stat().st_mtime)
        _upload_then_publish(
            kind="vsix",
            artifacts=vsix[-1:] if vsix else [],
            root=root,
            dry_run=dry_run,
        )
