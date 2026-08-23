# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lint report formatting."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import (
    LANGS,
    RECOMMENDED_I18N_LINGUAS,
    RECOMMENDED_I18N_SOURCE,
    TEMPLATE_PUFF,
    _is_zfr_cli_package,
    _is_zfr_meta_repo,
    changelog_version,
    detect_lang,
    find_project_dir,
    is_probably_text,
    iter_files,
    template_dir,
    version_file_version,
)
from ..csr import Csr
from ..packaging import _meson_project_fields, _parse_control_stanzas
from .finding import Finding
from .util import *  # noqa: F403
from .util import *  # noqa: F403

def _next_steps(findings: list[Finding]) -> list[str]:
    steps: list[str] = []
    seen: set[str] = set()
    for f in findings:
        if f.severity not in ("error", "warn") or not f.fix:
            continue
        key = f.code
        if key in seen:
            continue
        seen.add(key)
        loc = f.file or ""
        if f.line:
            loc = f"{loc}:{f.line}"
        prefix = f"{loc}: " if loc else ""
        parts = [ln.strip() for ln in f.fix.strip().splitlines() if ln.strip()]
        summary = parts[0]
        if len(parts) > 1 and len(summary) < 60:
            summary = f"{summary} {parts[1]}"
        steps.append(f"{prefix}{summary}")
        if len(steps) >= 12:
            break
    return steps


def format_report(
    root: Path,
    name: str,
    lang: str,
    role: str,
    findings: list[Finding],
    *,
    verbose: bool = False,
    quiet: bool = False,
    color: str = "auto",
) -> str:
    csr = Csr(color)
    counts = {k: 0 for k in ("error", "warn", "note", "ok")}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    failed = counts["error"] > 0
    status = "FAIL" if failed else "PASS"
    status_s = csr.sev("error" if failed else "ok", status)

    lines: list[str] = []
    head = csr.wrap("zfr lint", csr.bold)
    lines.append(
        f"{head}: {root}  name={name}  lang={lang}  role={role}"
    )
    lines.append(
        f"status: {status_s}  "
        f"{csr.sev('error', 'errors=' + str(counts['error']))}  "
        f"{csr.sev('warn', 'warnings=' + str(counts['warn']))}  "
        f"notes={counts['note']}"
    )
    if not quiet:
        role_hint = {
            "meta": "zephyr meta-repo (templates + CLI tools)",
            "template": "language template inside the meta-repo (placeholders like zephyr/some_puff1 are expected)",
            "app": "project instantiated from a language template (directory name must match meson/debian; no leftover zephyr/some_puff1 tokens)",
        }.get(role, role)
        lines.append(csr.wrap(f"role: {role_hint}", csr.dim))
        lines.append("")
        lines.append(csr.wrap("Zephyr style (finish the project to this contract)", csr.bold, csr.magenta))
        for item in (
            "License AGPL-3.0-or-later (meson license, debian/copyright AGPL-3+, rpm License).",
            "Build with Meson; debian/rules uses dh --buildsystem=meson --builddirectory=debian/build.",
            "project() version from `zfr version`; keep fallback v=\"0.0.0\" # FIXED TO 0.0.0, DO NOT MODIFY.",
            "Man pages: docs/*.adoc + asciidoctor -b manpage; translated pages under share/man/<locale>/man1.",
            "Packaging: debian/control Build-Depends meson, ninja-build, asciidoctor; optional rpm/ aligned with debian.",
            "i18n: English source; po/LINGUAS at least ar bn de es fr hi id it ja ko pt ru sv ta te th tr ur vi zh_CN zh_TW.",
            "Apps: `zfr rename <dir>` then `zfr add <puff>`; VERSION matches debian/changelog (git describe may differ).",
        ):
            lines.append(f"  - {item}")
    lines.append("")

    order = {"error": 0, "warn": 1, "note": 2, "ok": 3}
    shown = [f for f in findings if f.severity != "ok" or verbose]
    if quiet:
        shown = [f for f in shown if f.severity == "error"]
    shown.sort(key=lambda f: (order.get(f.severity, 9), f.file or "", f.line or 0, f.code))

    for f in shown:
        loc = f.file or ""
        if f.line:
            loc = f"{loc}:{f.line}"
        tag = csr.sev(f.severity, f"{f.severity:5}")
        code = csr.wrap(f.code, csr.dim)
        loc_s = csr.wrap(loc, csr.bold, csr.blue) if loc else ""
        extra = f"  {loc_s}" if loc_s else ""
        lines.append(f"{tag}  {code}{extra}")
        lines.append(f"      {f.message}")
        if f.fix:
            for i, fl in enumerate(f.fix.strip().splitlines()):
                prefix = "      fix: " if i == 0 else "           "
                lines.append(csr.wrap(prefix + fl, csr.dim))
        lines.append("")

    steps = _next_steps(findings)
    if not quiet:
        if steps:
            lines.append(csr.wrap("Next steps (zephyr style)", csr.bold, csr.magenta))
            for i, step in enumerate(steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")
        lines.append(
            csr.wrap(
                "Hint: after edits, re-run `zfr lint` from the project (or a subdirectory). "
                "`zfr about -d -r` dumps packaging fields. Version for Meson/RPM is `zfr version`. "
                "`zfr ize` applies missing debian/rpm/meson/man/version-subst upgrades.",
                csr.dim,
            )
        )
    return "\n".join(lines).rstrip() + "\n"
