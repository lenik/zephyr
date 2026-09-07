# SPDX-License-Identifier: AGPL-3.0-or-later
"""Severity remapping for zfr lint (-w/--warning, -e/--error)."""

from __future__ import annotations

import argparse

from ..finding import Finding
from ..i18n import _

# CLI names → Finding.severity (`info` accepted as alias for `note`).
_LEVEL_ALIASES = {
    "note": "note",
    "info": "note",
    "warn": "warn",
    "warning": "warn",
    "error": "error",
}
_ORDER = {"note": 0, "warn": 1, "error": 2}


def parse_severity_level(value: str) -> str:
    """Parse note|warn|error → Finding.severity."""
    key = (value or "").strip().lower()
    if key not in _LEVEL_ALIASES:
        raise argparse.ArgumentTypeError(
            _("invalid severity level %r (want note, warn, or error)") % value
        )
    return _LEVEL_ALIASES[key]


def remap_severities(
    findings: list[Finding],
    *,
    as_warning: str | None = None,
    as_error: str | None = None,
) -> list[Finding]:
    """Remap finding severities in place; return the same list.

    *-w/--warning=LEVEL*: treat that LEVEL as warn
      (note→warn; warn no-op; error→warn).

    *-e/--error=LEVEL*: treat LEVEL and more severe below error as error
      (note→ note+warn→error; warn→warn→error; error no-op).

    When both apply to the same finding, *-e* wins.
    """
    for f in findings:
        if f.severity not in _ORDER:
            continue
        orig = f.severity
        new = orig
        if as_error and as_error != "error":
            o = _ORDER[orig]
            if _ORDER[as_error] <= o < _ORDER["error"]:
                new = "error"
        elif as_warning and as_warning != "warn" and orig == as_warning:
            new = "warn"
        f.severity = new
    return findings
