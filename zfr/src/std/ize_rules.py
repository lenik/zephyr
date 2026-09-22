# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered zephyr ize rules (ZI0001+) — discovered from ize/rules/ZI*/rule.py."""

from __future__ import annotations

from lint.base import discover_rules, specs_to_std_rules

_SPECS = discover_rules("ize", prefix="ZI")
IZE_RULES = specs_to_std_rules(_SPECS)


def ize_rule_id(code: str) -> str:
    return IZE_RULES.rule_id(code)


def all_ize_specs():
    return _SPECS
