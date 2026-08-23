# SPDX-License-Identifier: AGPL-3.0-or-later
"""Debian packaging checks."""

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

def check_debian(root: Path, lang: str, role: str) -> list[Finding]:
    out: list[Finding] = []
    src, pkg, text = _control(root)
    rel = "debian/control"
    if not text:
        return out

    bd = src.get("Build-Depends", "")
    for dep in ("meson", "ninja-build", "asciidoctor"):
        if re.search(rf"\b{re.escape(dep)}\b", bd):
            out.append(Finding("ok", f"debian.build-depends.{dep}", f"Build-Depends has {dep}", rel))
        else:
            out.append(
                Finding(
                    "error",
                    f"debian.build-depends.{dep}",
                    f"Build-Depends missing {dep}",
                    rel,
                    fix=f"Add {dep} to Build-Depends (zephyr packages build with Meson + AsciiDoc man pages).",
                )
            )
    if "debhelper-compat" in bd:
        out.append(Finding("ok", "debian.debhelper", "debhelper-compat present", rel))
    else:
        out.append(
            Finding(
                "warn",
                "debian.debhelper",
                "Build-Depends missing debhelper-compat (= 13)",
                rel,
                fix="Build-Depends: debhelper-compat (= 13), meson, ninja-build, asciidoctor",
            )
        )

    arch = pkg.get("Architecture", "")
    if not arch:
        out.append(
            Finding(
                "error",
                "debian.Architecture",
                "Package stanza missing Architecture",
                rel,
                fix="Architecture: all  (scripts) or any (compiled).",
            )
        )
    elif lang == "bash" and arch != "all":
        out.append(
            Finding(
                "warn",
                "debian.Architecture",
                f"bash packages should be Architecture: all (got {arch})",
                rel,
                fix="Architecture: all",
            )
        )
    elif lang in ("c", "clib", "cpp", "cpplib", "rust", "go", "haskell") and arch == "all":
        out.append(
            Finding(
                "warn",
                "debian.Architecture",
                f"{lang} packages are usually Architecture: any (got all)",
                rel,
                fix="Architecture: any",
            )
        )
    else:
        out.append(Finding("ok", "debian.Architecture", f"Architecture: {arch}", rel))

    homepage = src.get("Homepage", "")
    if homepage:
        out.append(Finding("ok", "debian.Homepage", f"Homepage: {homepage}", rel))
    else:
        out.append(
            Finding(
                "warn",
                "debian.Homepage",
                "no Homepage",
                rel,
                fix="Set Homepage: to the project URL.",
            )
        )

    rules = _read(root / "debian" / "rules")
    if "buildsystem=meson" in rules and "debian/build" in rules:
        out.append(Finding("ok", "debian.rules", "dh meson debian/build", "debian/rules"))
    elif rules:
        out.append(
            Finding(
                "warn",
                "debian.rules",
                "debian/rules is not dh --buildsystem=meson --builddirectory=debian/build",
                "debian/rules",
                fix="Use:\n#!/usr/bin/make -f\n\n%:\n\tdh $@ --buildsystem=meson --builddirectory=debian/build",
            )
        )

    copyr = _read(root / "debian" / "copyright")
    if "AGPL" in copyr:
        out.append(Finding("ok", "debian.copyright", "copyright mentions AGPL", "debian/copyright"))
    elif copyr:
        out.append(
            Finding(
                "warn",
                "debian.copyright",
                "debian/copyright does not mention AGPL",
                "debian/copyright",
                fix="Use the template debian/copyright (License: AGPL-3+).",
            )
        )

    fmt = _read(root / "debian" / "source" / "format").strip()
    if fmt:
        out.append(Finding("ok", "debian.source.format", f"source format {fmt}", "debian/source/format"))

    ch_ver = changelog_version(root)
    file_ver = version_file_version(root)
    if ch_ver and file_ver and ch_ver.lstrip("v") != file_ver.lstrip("v"):
        out.append(
            Finding(
                "warn",
                "debian.VERSION_sync",
                f"VERSION={file_ver!r} != changelog {ch_ver!r}",
                "VERSION",
                fix="VERSION should match the latest debian/changelog entry "
                "(pre-commit hook updates it). Git describe may still differ.",
            )
        )
    elif ch_ver and file_ver:
        out.append(
            Finding("ok", "debian.VERSION_sync", f"VERSION matches changelog {ch_ver}", "VERSION")
        )

    if lang == "bash":
        deps = pkg.get("Depends", "")
        if "bash-shlib" not in deps:
            out.append(
                Finding(
                    "error",
                    "debian.Depends.bash-shlib",
                    "bash project Depends missing bash-shlib",
                    rel,
                    fix="Depends: bash, bash-shlib, ${misc:Depends}",
                )
            )
        else:
            out.append(Finding("ok", "debian.Depends.bash-shlib", "Depends includes bash-shlib", rel))
    return out
