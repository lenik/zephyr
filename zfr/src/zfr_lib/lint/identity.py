# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project identity checks."""

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

def check_identity(root: Path, lang: str, role: str) -> list[Finding]:
    out: list[Finding] = []
    meson = _meson_project_fields(root)
    src, pkg, _ = _control(root)
    dir_name = root.name
    meson_name = meson.get("name") or ""
    source = src.get("Source") or ""
    package = pkg.get("Package") or ""

    names = {
        "directory": dir_name,
        "meson.project": meson_name,
        "debian.Source": source,
        "debian.Package": package,
    }
    if role == "app":
        expected = dir_name
        for label, val in names.items():
            if not val:
                continue
            if val != expected:
                out.append(
                    Finding(
                        "error",
                        f"identity.{label}",
                        f"{label} is {val!r}, expected {expected!r} (directory name)",
                        "meson.build" if label.startswith("meson") else "debian/control",
                        fix=f"Set {label} to {expected!r}, or rename the directory. "
                        "Use `zfr rename {expected}` if leftover template names remain.",
                    )
                )
            else:
                out.append(Finding("ok", f"identity.{label}", f"{label}={val}"))
    else:
        if meson_name:
            out.append(Finding("ok", "identity.meson.project", f"meson project name={meson_name}"))
        if source and meson_name and source != meson_name:
            out.append(
                Finding(
                    "warn",
                    "identity.source_vs_meson",
                    f"debian Source={source!r} != meson project={meson_name!r}",
                    "debian/control",
                    fix="Keep Source, Package, and meson project() name identical.",
                )
            )
        elif source:
            out.append(Finding("ok", "identity.debian.Source", f"Source={source}"))

    specs = _specs(root)
    if specs:
        text = _read(specs[0])
        m = re.search(r"^Name:\s*(\S+)", text, re.M)
        spec_name = m.group(1) if m else ""
        want = source or meson_name or dir_name
        if spec_name and want and spec_name != want:
            out.append(
                Finding(
                    "error",
                    "identity.rpm.Name",
                    f"spec Name={spec_name!r} != debian/meson name {want!r}",
                    _rel(root, specs[0]),
                    line=_line_of(text, "Name:"),
                    fix=f"Set Name: {want} in the spec (same as debian Source).",
                )
            )
        elif spec_name:
            out.append(Finding("ok", "identity.rpm.Name", f"spec Name={spec_name}", _rel(root, specs[0])))
    return out
