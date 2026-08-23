
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A single zfr lint finding."""

from __future__ import annotations

from dataclasses import dataclass

@dataclass
class Finding:
    severity: str  # error, warn, note, ok
    code: str
    message: str
    file: str | None = None
    line: int | None = None
    fix: str | None = None
