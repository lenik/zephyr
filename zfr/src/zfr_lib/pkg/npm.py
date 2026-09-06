# SPDX-License-Identifier: AGPL-3.0-or-later
"""npm / vsix packager implementation."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..cmd_run import run_cmd
from ..stream_mark import log_line
from .provider import PackagerContext


class NpmPackager:
    """Builds ``npm`` or ``vsix`` via pnpm/npm ``package`` script."""

    def __init__(self, kind: str = "npm") -> None:
        if kind not in {"npm", "vsix"}:
            raise ValueError(f"unsupported npm-family kind: {kind!r}")
        self._kind = kind

    @property
    def name(self) -> str:
        return self._kind

    def build(self, ctx: PackagerContext) -> bool:
        runner = shutil.which("pnpm") or shutil.which("npm")
        if not runner:
            raise SystemExit("zfr package: pnpm/npm not found in PATH")
        log_line(f"zfr package: building {self._kind}")
        if Path(runner).name == "pnpm":
            run_cmd([runner, "package"], cwd=ctx.root, dry_run=ctx.dry_run)
        else:
            run_cmd([runner, "run", "package"], cwd=ctx.root, dry_run=ctx.dry_run)
        return True


def package_npm_or_vsix(root: Path, kind: str, *, dry_run: bool = False) -> None:
    NpmPackager(kind).build(PackagerContext(root=Path(root), dry_run=dry_run))
