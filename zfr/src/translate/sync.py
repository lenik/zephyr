# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sync gettext catalogs from sources (replaces scripts/posync.sh)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from lib import find_project_dir


def _pot_name(root: Path) -> str:
    control = root / "debian" / "control"
    if control.is_file():
        for line in control.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.lower().startswith("source:"):
                name = line.split(":", 1)[1].strip()
                if name:
                    return f"{name}.pot"
    meson = root / "meson.build"
    if meson.is_file():
        m = re.search(r"project\s*\(\s*['\"]([^'\"]+)['\"]", meson.read_text(encoding="utf-8", errors="ignore"))
        if m:
            return f"{m.group(1)}.pot"
    return f"{root.name}.pot"


def _python_sources(root: Path) -> list[str]:
    """Paths relative to *root* for xgettext (src/**/*.py + extensionless entrypoints)."""
    src = root / "src"
    files: list[str] = []
    if src.is_dir():
        for path in sorted(src.rglob("*.py")):
            files.append(str(path.relative_to(root)))
        for path in sorted(src.iterdir()):
            if not path.is_file() or path.suffix:
                continue
            try:
                first = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
            except OSError:
                continue
            if first and "python" in first[0]:
                files.append(str(path.relative_to(root)))
    potfiles = root / "po" / "POTFILES"
    if potfiles.is_file() and not files:
        for line in potfiles.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                files.append(line)
    return files


def _run(cmd: list[str], *, cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def sync_catalogs(root: Path | None = None) -> int:
    """Extract msgids and merge into po/*.po (msgmerge --no-wrap). Return process status."""
    if root is None:
        env_root = os.environ.get("MESON_SOURCE_ROOT") or os.environ.get("SOURCE_ROOT")
        root = Path(env_root).resolve() if env_root else find_project_dir()
    root = root.resolve()
    po_dir = root / "po"
    if not po_dir.is_dir():
        print(f"zfr translate --sync: no po/ under {root}", flush=True)
        return 1

    linguas = po_dir / "LINGUAS"
    if not linguas.is_file():
        print(f"zfr translate --sync: missing {linguas}", flush=True)
        return 1

    sources = _python_sources(root)
    if not sources:
        print("zfr translate --sync: no Python sources to extract", flush=True)
        return 1

    pot = po_dir / _pot_name(root)
    xgettext = shutil.which("xgettext")
    if not xgettext:
        print("zfr translate --sync: xgettext not found", flush=True)
        return 1

    _run(
        [
            xgettext,
            "--from-code=UTF-8",
            "--keyword=_",
            "--language=Python",
            f"--directory={root}",
            f"--output={pot.name}",
            *sources,
        ],
        cwd=po_dir,
    )

    msginit = shutil.which("msginit")
    msgmerge = shutil.which("msgmerge")
    msgattrib = shutil.which("msgattrib")
    if not msgmerge or not msgattrib:
        print("zfr translate --sync: msgmerge/msgattrib required", flush=True)
        return 1

    for raw in linguas.read_text(encoding="utf-8", errors="ignore").splitlines():
        lang = raw.strip()
        if not lang or lang.startswith("#"):
            continue
        po_file = po_dir / f"{lang}.po"
        if not po_file.is_file():
            if not msginit:
                print(f"zfr translate --sync: msginit missing; cannot create {po_file.name}", flush=True)
                return 1
            _run(
                [
                    msginit,
                    "--no-translator",
                    f"--input={pot.name}",
                    f"--locale={lang}",
                    f"--output-file={po_file.name}",
                ],
                cwd=po_dir,
            )
        _run(
            [
                msgmerge,
                "--update",
                "--backup=none",
                "--no-wrap",
                po_file.name,
                pot.name,
            ],
            cwd=po_dir,
        )
        # msgattrib truncates if -o is the same path; write via tempfile.
        fd, tmp_name = tempfile.mkstemp(prefix=f"{lang}.", suffix=".po", dir=po_dir)
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            _run(
                [
                    msgattrib,
                    "--no-obsolete",
                    "--no-wrap",
                    f"--output-file={tmp_path.name}",
                    po_file.name,
                ],
                cwd=po_dir,
            )
            tmp_path.replace(po_file)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    print(f"zfr translate --sync: updated {pot.relative_to(root)} and LINGUAS catalogs", flush=True)
    return 0


def sync_main(argv: list[str] | None = None) -> int:
    """CLI/meson entry: optional root path as argv[1]."""
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]).resolve() if args else None
    return sync_catalogs(root)


if __name__ == "__main__":
    raise SystemExit(sync_main())
