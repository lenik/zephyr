# SPDX-License-Identifier: AGPL-3.0-or-later
"""GitHub Actions release-packages scaffold checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

from i18n import _
from .finding import Finding

_WORKFLOW = Path(".github/workflows/release-packages.yml")
_MATRIX = Path("scripts/ci/matrix.json")
_BUILD_RPM = Path("scripts/ci/build-rpm.sh")
_REQUIRED_SCRIPTS = (
    "scripts/ci/matrix.json",
    "scripts/ci/matrix-from-json.sh",
    "scripts/ci/build-deb.sh",
    "scripts/ci/build-rpm.sh",
    "scripts/ci/publish-private.sh",
)


def check_ci(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    wf = root / _WORKFLOW
    if not wf.is_file():
        findings.append(
            Finding(
                "note",
                "ci.release_workflow",
                _("missing %(path)s (multi-distro release package builds)")
                % {"path": _WORKFLOW.as_posix()},
                fix=_(
                    "Run `zfr ize` or `zfr create` to install the shared CI scaffold "
                    "from zfr share/ci (ubuntu-latest + Docker; no build4/zfr in YAML)."
                ),
            )
        )
        return findings

    text = wf.read_text(encoding="utf-8", errors="ignore")
    if "release:" not in text or "published" not in text:
        findings.append(
            Finding(
                "warn",
                "ci.release_workflow",
                _("%(path)s should trigger on release published")
                % {"path": _WORKFLOW.as_posix()},
                fix=_("Keep `on: release: types: [published]` in the workflow."),
            )
        )
    # Guardrails: YAML must stay tooling-agnostic.
    lowered = text.lower()
    for banned in ("build4", "b4f-", "zfr "):
        if banned in lowered:
            findings.append(
                Finding(
                    "warn",
                    "ci.release_workflow",
                    _("%(path)s should not reference %(token)s")
                    % {"path": _WORKFLOW.as_posix(), "token": banned.strip()},
                    fix=_("Build with stock Docker images and dpkg-buildpackage/rpmbuild only."),
                )
            )

    if "REPODEB_COMPONENT: contrib" in text or "REPODEB_COMPONENT:contrib" in text:
        findings.append(
            Finding(
                "warn",
                "ci.release_workflow",
                _("release workflow still uses apt component contrib"),
                fix=_("Use REPODEB_COMPONENT: main (repodeb_aptly default component)."),
            )
        )
    elif "REPODEB_COMPONENT: main" in text or "REPODEB_COMPONENT:main" in text:
        findings.append(
            Finding(
                "ok",
                "ci.release_workflow",
                _("release workflow uses apt component main"),
            )
        )

    missing = [p for p in _REQUIRED_SCRIPTS if not (root / p).is_file()]
    if missing:
        findings.append(
            Finding(
                "note",
                "ci.release_scripts",
                _("missing CI helper scripts: %(paths)s")
                % {"paths": ", ".join(missing)},
                fix=_("Install scripts/ci/* from zfr share/ci via `zfr ize`."),
            )
        )
    else:
        findings.append(
            Finding(
                "ok",
                "ci.release_scripts",
                _("release CI helper scripts under scripts/ci/ are present"),
            )
        )
        findings.append(
            Finding(
                "ok",
                "ci.release_workflow",
                _("release-packages GitHub Actions workflow is present"),
            )
        )
        findings.extend(_check_matrix(root))
        findings.extend(_check_build_rpm(root))
    return findings


def _check_matrix(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    path = root / _MATRIX
    if not path.is_file():
        return findings
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(
            Finding(
                "error",
                "ci.matrix_arch",
                _("scripts/ci/matrix.json is not valid JSON: %(err)s") % {"err": exc},
                fix=_("Fix JSON syntax in scripts/ci/matrix.json."),
            )
        )
        return findings

    bad_armhf: list[str] = []
    bad_loong: list[str] = []
    for cell in data.get("deb") or []:
        if not isinstance(cell, dict):
            continue
        family = str(cell.get("family") or "")
        release = str(cell.get("release") or "")
        arch = str(cell.get("arch") or "")
        platform = str(cell.get("platform") or "")
        label = f"{release}/{arch}"
        if arch == "armhf" and family != "raspi":
            bad_armhf.append(label)
        if arch == "armhf" and family == "raspi" and "arm/v6" not in platform:
            findings.append(
                Finding(
                    "warn",
                    "ci.matrix_arch",
                    _("raspi cell %(label)s should use platform linux/arm/v6 (ARMv6+VFPv2)")
                    % {"label": label},
                    fix=_(
                        "Set platform to linux/arm/v6 for raspi_* (not linux/arm/v7 "
                        "Debian armhf)."
                    ),
                )
            )
        if arch in {"loong64", "loongarch64"} and family not in {"uos", "kylin"}:
            bad_loong.append(label)

    if bad_armhf:
        findings.append(
            Finding(
                "warn",
                "ci.matrix_arch",
                _("armhf is raspi-only; unexpected cells: %(cells)s")
                % {"cells": ", ".join(bad_armhf)},
                fix=_(
                    "Keep armhf only for raspi_bookworm (linux/arm/v6). "
                    "Debian/Ubuntu matrix cells must not use armhf."
                ),
            )
        )
    if bad_loong:
        findings.append(
            Finding(
                "warn",
                "ci.matrix_arch",
                _("loong64 is uos/kylin-only; unexpected cells: %(cells)s")
                % {"cells": ", ".join(bad_loong)},
                fix=_(
                    "Keep loong64 only for uos_* / kylin_* (and those families "
                    "should be loong64-only)."
                ),
            )
        )
    if not bad_armhf and not bad_loong:
        findings.append(
            Finding(
                "ok",
                "ci.matrix_arch",
                _("matrix.json arch policy: raspi=armhf/v6, uos/kylin=loong64"),
            )
        )
    return findings


def _check_build_rpm(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    path = root / _BUILD_RPM
    if not path.is_file():
        return findings
    text = path.read_text(encoding="utf-8", errors="ignore")
    has_map = "bash-builtins" in text and (
        "bash.pc" in text or "aliased" in text or "Name: bash-builtins" in text
    )
    if not has_map:
        findings.append(
            Finding(
                "warn",
                "ci.rpm_deb_deps",
                _("build-rpm.sh should map Debian bash-builtins → bash + bash.pc"),
                fix=_(
                    "On RPM, bash-builtins is provided by the bash package "
                    "(bash.pc). Alias bash.pc to bash-builtins.pc before meson; "
                    "see zfr share/ci/scripts/ci/build-rpm.sh."
                ),
            )
        )
    else:
        findings.append(
            Finding(
                "ok",
                "ci.rpm_deb_deps",
                _("build-rpm.sh maps bash-builtins via bash (experiential)"),
            )
        )
    return findings
