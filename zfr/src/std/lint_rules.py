# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered zephyr lint rules (ZL0001+) — discovered from lint/rules/ZL*/rule.py."""

from __future__ import annotations

from lint.base import discover_rules, specs_to_std_rules

_SPECS = discover_rules("lint", prefix="ZL")
LINT_RULES = specs_to_std_rules(_SPECS)


def lint_rule_id(code: str) -> str:
    return LINT_RULES.rule_id(code)


def all_lint_specs():
    return _SPECS
