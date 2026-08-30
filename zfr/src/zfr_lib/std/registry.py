# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered zfr lint/ize standard rules and suppression helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StdRule:
    id: str
    code: str
    title: str
    default_severity: str | None = None


class RuleRegistry:
    def __init__(self, rules: tuple[StdRule, ...]) -> None:
        self._rules = rules
        self._exact = {r.code: r for r in rules if not r.code.endswith("*")}
        self._patterns = [r for r in rules if r.code.endswith("*")]

    def lookup(self, code: str) -> StdRule | None:
        if code in self._exact:
            return self._exact[code]
        best: StdRule | None = None
        best_len = -1
        for rule in self._patterns:
            prefix = rule.code[:-1]
            if code.startswith(prefix) and len(prefix) > best_len:
                best = rule
                best_len = len(prefix)
        return best

    def rule_id(self, code: str) -> str:
        rule = self.lookup(code)
        return rule.id if rule is not None else "ZL???"

    def all_rules(self) -> tuple[StdRule, ...]:
        return self._rules


def parse_uncheck(values: list[str] | None) -> set[str]:
    out: set[str] = set()
    if not values:
        return out
    for raw in values:
        for piece in raw.split(","):
            token = piece.strip()
            if token:
                out.add(token)
    return out


def is_suppressed(
    *,
    rule_id: str,
    code: str,
    suppressed: set[str],
) -> bool:
    if not suppressed:
        return False
    if rule_id in suppressed or code in suppressed:
        return True
    rid = rule_id.upper()
    if rid in {s.upper() for s in suppressed}:
        return True
    return False


def render_std_markdown(
    *,
    title: str,
    intro: str,
    rules: tuple[StdRule, ...],
) -> str:
    lines = [
        f"# {title}",
        "",
        intro,
        "",
        "| ID | Code | Default | Title |",
        "|----|------|---------|-------|",
    ]
    for rule in rules:
        sev = rule.default_severity or "varies"
        lines.append(f"| {rule.id} | `{rule.code}` | {sev} | {rule.title} |")
    lines.append("")
    lines.append(
        "Suppress rules with `zfr lint -u ID` / `zfr ize -u ID` "
        "(comma-separated), or the same flag in `.config/zfr/lint.options` / "
        "`.config/zfr/ize.options`."
    )
    lines.append("")
    return "\n".join(lines)
