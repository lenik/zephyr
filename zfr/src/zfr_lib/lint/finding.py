# SPDX-License-Identifier: AGPL-3.0-or-later
"""Re-export Finding (defined in zfr_lib.finding to avoid import cycles)."""

from __future__ import annotations

from ..finding import Finding

__all__ = ["Finding"]
