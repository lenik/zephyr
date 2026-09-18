# SPDX-License-Identifier: AGPL-3.0-or-later
"""Filter and format lint findings."""

from __future__ import annotations

from ..finding import Finding
from ..std import is_suppressed, lint_rule_id, parse_uncheck


def filter_findings(
    findings: list[Finding],
    uncheck: list[str] | None,
    always: list[str] | None = None,
) -> list[Finding]:
    suppressed = parse_uncheck(uncheck)
    forced = parse_uncheck(always)
    if not suppressed and not forced:
        return findings
    out: list[Finding] = []
    for finding in findings:
        rid = lint_rule_id(finding.code)
        if forced and is_suppressed(rule_id=rid, code=finding.code, suppressed=forced):
            out.append(finding)
            continue
        if is_suppressed(rule_id=rid, code=finding.code, suppressed=suppressed):
            continue
        out.append(finding)
    return out
