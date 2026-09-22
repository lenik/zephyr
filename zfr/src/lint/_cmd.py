# SPDX-License-Identifier: AGPL-3.0-or-later
"""lint command implementation (import-light package entry stays in __init__)."""

from __future__ import annotations

import sys
from pathlib import Path

from finding import Finding
from lib import _is_zfr_cli_package, find_project_dir
from pkgfields import _meson_project_fields
from lint.filtering import filter_findings
from lint.report import format_report
from lint.severity import remap_severities
from lint.util import _control, _role


def _resolve_lint_root(root: Path) -> Path:
    """Lint the zfr CLI package when cwd is the zephyr meta-repo root."""
    if _role(root) == "meta":
        cli = root / "zfr"
        if _is_zfr_cli_package(cli):
            return cli
    return root


def collect_findings(
    root: Path, *, l10n_level: str = "L1"
) -> tuple[str, str, str, list[Finding]]:
    """Scan project, schedule rules, call each rule.lint(files, session)."""
    from std.lint_rules import all_lint_specs
    from lint.scanner import scan_project, select_scheduled
    from lint.session import Session

    root = _resolve_lint_root(root)
    role = _role(root)
    if role == "meta":
        lang = "meta"
    else:
        try:
            from lib import detect_lang

            lang = detect_lang(root)
        except SystemExit:
            lang = "unknown"
    meson = _meson_project_fields(root)
    src, _pkg, _ctl = _control(root)
    name = src.get("Source") or meson.get("name") or root.name

    session = Session(
        root=root,
        lang=lang,
        role=role,
        l10n_level=l10n_level,
        name=name,
    )
    rules = all_lint_specs()
    _file_to_rules, rule_to_files = scan_project(root, rules, session)
    scheduled = select_scheduled(rules, rule_to_files, require_files=True)

    findings: list[Finding] = []
    seen: set[tuple[str, str | None, int | None, str]] = set()
    for spec, files in scheduled:
        for f in spec.lint(files, session):
            key = (f.code, f.file, f.line, f.message)
            if key in seen:
                continue
            seen.add(key)
            findings.append(f)
    return name, lang, role, findings


def cmd_lint(
    *,
    verbose: bool = False,
    quiet: bool = False,
    color: str = "auto",
    warning_level: str | None = None,
    error_level: str | None = None,
    l10n_level: str = "L1",
    style_info: bool | None = None,
    for_ai_purpose: bool | None = None,
    workdir: Path | None = None,
    uncheck: list[str] | None = None,
    always: list[str] | None = None,
    browse: bool = False,
) -> int:
    from terminal import resolve_for_ai_purpose

    root = _resolve_lint_root(find_project_dir(workdir))
    if browse:
        from lint.browse import browse_lint

        return browse_lint(
            root,
            l10n_level=l10n_level,
            uncheck=uncheck,
            always=always,
            warning_level=warning_level,
            error_level=error_level,
        )
    name, lang, role, findings = collect_findings(root, l10n_level=l10n_level)
    findings = filter_findings(findings, uncheck, always)
    remap_severities(findings, as_warning=warning_level, as_error=error_level)
    ai = resolve_for_ai_purpose(for_ai_purpose)
    sys.stdout.write(
        format_report(
            root,
            name,
            lang,
            role,
            findings,
            verbose=verbose,
            quiet=quiet,
            color=color,
            style_info=style_info,
            for_ai_purpose=ai,
        )
    )
    sys.stdout.flush()
    if any(f.severity == "error" for f in findings):
        return 1
    return 0
