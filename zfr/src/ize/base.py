# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize rule discovery (mirrors lint.base)."""

from __future__ import annotations

from lint.base import RuleSpec, discover_rules, load_rule_module, specs_to_std_rules

__all__ = ["RuleSpec", "discover_rules", "load_rule_module", "specs_to_std_rules"]


def discover_ize_rules() -> list[RuleSpec]:
    return discover_rules("ize", prefix="ZI")
