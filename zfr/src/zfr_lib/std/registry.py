# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered zfr lint/ize standard rules and suppression helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StdRule:
    id: str
    code: str
    title: str
    default_severity: str | None = None
    detail: str | None = None


class RuleRegistry:
    def __init__(self, rules: tuple[StdRule, ...]) -> None:
        self._rules = rules
        self._exact = {r.code: r for r in rules if not r.code.endswith("*")}
        self._patterns = [r for r in rules if r.code.endswith("*")]
        self._by_id = {r.id.upper(): r for r in rules}
        self._id_prefix = rules[0].id[:2] if rules else "Z?"

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

    def by_id(self, token: str) -> StdRule | None:
        """Resolve ``ZL026``, ``zl26``, ``26``, or a code like ``rpm.missing``."""
        raw = token.strip()
        if not raw:
            return None
        upper = raw.upper()
        if upper in self._by_id:
            return self._by_id[upper]
        m = re.fullmatch(r"(?:ZL|ZI)?(\d{1,3})", upper)
        if m:
            cand = f"{self._id_prefix}{int(m.group(1)):03d}"
            if cand in self._by_id:
                return self._by_id[cand]
        return self.lookup(raw)

    def rule_id(self, code: str) -> str:
        rule = self.lookup(code)
        if rule is not None:
            return rule.id
        return f"{self._id_prefix}???"

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


def render_std_table(rules: tuple[StdRule, ...]) -> str:
    """Plain-text table of standard rules (ID / code / default / title)."""
    rows = [
        (r.id, r.code, r.default_severity or "varies", r.title) for r in rules
    ]
    headers = ("ID", "Code", "Default", "Title")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    sep = "  ".join("-" * w for w in widths)
    lines = [
        "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)),
        sep,
    ]
    for row in rows:
        lines.append("  ".join(row[i].ljust(widths[i]) for i in range(4)))
    lines.append("")
    return "\n".join(lines)


def render_std_help(rule: StdRule, *, command: str) -> str:
    """Multi-line detail for one standard rule (``zfr {lint|ize} -H``)."""
    sev = rule.default_severity or "varies"
    lines = [
        f"ID:       {rule.id}",
        f"Code:     {rule.code}",
        f"Default:  {sev}",
        f"Title:    {rule.title}",
    ]
    if rule.detail:
        lines.append("")
        lines.append(rule.detail.rstrip())
    lines.append("")
    lines.append(
        f"Suppress with `zfr {command} -u {rule.id}` or "
        f"`zfr {command} -u {rule.code}` "
        f"(also `.config/zfr/{command}.options`)."
    )
    lines.append(f"List all: `zfr {command} -L` / `zfr {command} --list-std`.")
    lines.append("")
    return "\n".join(lines)
