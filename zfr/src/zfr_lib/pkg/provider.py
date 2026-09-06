# SPDX-License-Identifier: AGPL-3.0-or-later
"""Packager provider interface and shared build context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class PackagerContext:
    """Inputs shared by every packager implementation."""

    root: Path
    jobs: int = 1
    dry_run: bool = False
    dpkg_buildopts: list[str] = field(default_factory=list)
    docker: bool = False
    docker_server: str = ""
    base_image: str = "b4f-debian:trixie"


@runtime_checkable
class Packager(Protocol):
    """Provider interface: one packaging kind (deb, rpm, npm, …)."""

    @property
    def name(self) -> str:
        """Canonical kind id (``deb``, ``rpm``, …)."""

    def build(self, ctx: PackagerContext) -> bool:
        """Build this kind under *ctx*.

        Returns True if a package was produced, False if skipped (no tools /
        no .build-host). Raises on hard failure.
        """
