# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deferred text edits produced by ize rules; applied once by zfr."""

from __future__ import annotations

import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TextEdit:
    """One filesystem mutation relative to the project root."""

    path: str
    kind: str  # write | delete | copy | chmod
    content: str | None = None
    detail: str = ""
    rule: str = ""
    source: str | None = None  # project-relative or absolute for copy
    mode: int | None = None


@dataclass
class EditList:
    edits: list[TextEdit] = field(default_factory=list)

    def write(
        self,
        path: str | Path,
        content: str,
        *,
        detail: str = "",
        rule: str = "",
        kind: str | None = None,
    ) -> None:
        rel = str(path).replace("\\", "/")
        self.edits.append(
            TextEdit(
                path=rel,
                kind=kind or "write",
                content=content,
                detail=detail,
                rule=rule,
            )
        )

    def delete(self, path: str | Path, *, detail: str = "", rule: str = "") -> None:
        rel = str(path).replace("\\", "/")
        self.edits.append(TextEdit(path=rel, kind="delete", detail=detail, rule=rule))

    def copy(
        self,
        source: str | Path,
        dest: str | Path,
        *,
        detail: str = "",
        rule: str = "",
        executable: bool = False,
    ) -> None:
        self.edits.append(
            TextEdit(
                path=str(dest).replace("\\", "/"),
                kind="copy",
                detail=detail,
                rule=rule,
                source=str(source),
                mode=(stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) if executable else None,
            )
        )

    def merge(self, other: EditList | None) -> EditList:
        if other is None:
            return self
        self.edits.extend(other.edits)
        return self

    def apply(self, root: Path, *, dry_run: bool = False) -> list[TextEdit]:
        """Apply edits under *root*. Returns the edits that were (or would be) applied."""
        applied: list[TextEdit] = []
        for ed in self.edits:
            dest = root / ed.path
            if ed.kind in ("write", "update", "add"):
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(ed.content or "", encoding="utf-8")
                applied.append(ed)
            elif ed.kind == "delete":
                if not dry_run and dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                applied.append(ed)
            elif ed.kind == "copy":
                if not dry_run and ed.source:
                    src = Path(ed.source)
                    if not src.is_absolute():
                        src = root / ed.source
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    if ed.mode is not None:
                        mode = dest.stat().st_mode
                        dest.chmod(mode | ed.mode)
                applied.append(ed)
            elif ed.kind == "chmod":
                if not dry_run and dest.is_file() and ed.mode is not None:
                    mode = dest.stat().st_mode
                    dest.chmod(mode | ed.mode)
                applied.append(ed)
        return applied
