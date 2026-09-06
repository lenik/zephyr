# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared helpers for the release pipeline."""

from __future__ import annotations

import os
import shlex
from pathlib import Path

# Re-export for convenience within the package.
from .logutil import quit, run  # noqa: F401


def default_options_files() -> list[Path]:
    """Candidate default-options paths (first existing wins when loading)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    bases = []
    if xdg:
        bases.append(Path(xdg))
    bases.append(Path.home() / ".config")
    names = ("zfr-release.options", "gh-makerelease.options")
    return [base / name for base in bases for name in names]


def default_options_file() -> Path:
    """Preferred path for writing/documenting defaults (may not exist yet)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "zfr-release.options"


def load_default_options(path: Path | None = None) -> list[str]:
    """Load default CLI tokens from the options file (CLI overrides).

    One token group per line (e.g. ``-p s1`` or ``--dput-host=bodz``).
    Blank lines and ``#`` comments are ignored.

    Prefers ``zfr-release.options``, then falls back to legacy
    ``gh-makerelease.options``.
    """
    if path is not None:
        candidates = [path]
    else:
        candidates = default_options_files()
    for cfg in candidates:
        if not cfg.is_file():
            continue
        result: list[str] = []
        with cfg.open(encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                result.extend(shlex.split(line))
        return result
    return []


def read_identity_token(path: str | Path) -> str | None:
    """First non-empty line from an identity file (trimmed), or None."""
    f = Path(path)
    if not f.is_file():
        return None
    with f.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line:
                return line
    return None
