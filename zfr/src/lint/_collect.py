# SPDX-License-Identifier: AGPL-3.0-or-later
"""Collect all lint findings once per session (shared by per-rule filters)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finding import Finding


def _code_matches(finding_code: str, pattern: str) -> bool:
    if pattern.endswith("*"):
        return finding_code.startswith(pattern[:-1])
    return finding_code == pattern or finding_code.startswith(pattern + ".")


def collect_all_findings(session: Any) -> list[Finding]:
    """Run legacy family checkers once and cache on the session."""
    cached = session.options.get("_all_findings")
    if cached is not None:
        return cached

    root: Path = session.root
    lang = session.lang
    role = session.role
    l10n_level = session.l10n_level

    from lint.debian import check_debian
    from lint.ci import check_ci
    from lint.gitignore import check_gitignore
    from lint.i18n_check import check_i18n
    from lint.identity import check_identity
    from lint.lang_bits import check_lang_bits
    from lint.layout import check_layout
    from lint.leftovers import check_leftovers, check_readme
    from lint.meson import check_meson
    from lint.rpm import check_rpm
    from lint.source_size import check_source_size
    from lint.template import check_template_gaps
    from lint.hardcoded import check_hardcoded
    from lint.scripts_check import check_scripts_and_version

    findings: list[Finding] = []
    findings.extend(check_layout(root, lang, role))
    findings.extend(check_gitignore(root, role))
    findings.extend(check_identity(root, lang, role))
    findings.extend(check_meson(root, lang))
    findings.extend(check_debian(root, lang, role))
    findings.extend(check_rpm(root, lang))
    findings.extend(check_readme(root, role))
    findings.extend(check_i18n(root, role, l10n_level=l10n_level))
    findings.extend(check_leftovers(root, role))
    findings.extend(check_lang_bits(root, lang))
    findings.extend(check_source_size(root, role))
    findings.extend(check_hardcoded(root, role))
    findings.extend(check_template_gaps(root, lang, role))
    findings.extend(check_scripts_and_version(root, role))
    findings.extend(check_ci(root))

    session.options["_all_findings"] = findings
    return findings


def filter_findings(session: Any, code_pattern: str) -> list[Finding]:
    """Return findings whose code matches this rule's CODE pattern."""
    return [f for f in collect_all_findings(session) if _code_matches(f.code, code_pattern)]
