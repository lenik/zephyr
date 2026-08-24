# SPDX-License-Identifier: AGPL-3.0-or-later
"""RPM packaging checks."""

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

def check_rpm(root: Path, lang: str) -> list[Finding]:
    out: list[Finding] = []
    specs = _specs(root)
    src, pkg, _ = _control(root)
    if not specs:
        out.append(
            Finding(
                "note",
                "rpm.missing",
                "no rpm/*.spec (optional, but zephyr style includes RPM next to debian/)",
                "rpm/",
                fix="Copy rpm/ from a language template; name the spec after the package "
                "(rpm/<Source>.spec, not zephyr.spec) and keep a Makefile using `zfr version`. "
                "Align Name/Summary/Requires/URL with debian/control. Or run `zfr ize`.",
            )
        )
        return out

    spec = specs[0]
    rel = _rel(root, spec)
    text = _read(spec)
    makefile = root / "rpm" / "Makefile"
    mk = _read(makefile)

    if "%{version}" in text or "%{!?version" in text:
        out.append(Finding("ok", "rpm.dynamic_version", "spec Version is dynamic %{version}", rel))
    elif re.search(r"^Version:\s*[0-9]", text, re.M):
        out.append(
            Finding(
                "error",
                "rpm.dynamic_version",
                "spec Version is hardcoded; zephyr style injects `zfr version`",
                rel,
                line=_line_of(text, "Version:"),
                fix="Use Version: %{version} with %{!?version:%global version 0.0.0} "
                "and freeze via rpm/Makefile (`zfr version` / `zfr version -r`).",
            )
        )

    if _AGPL in text:
        out.append(Finding("ok", "rpm.license", f"License {_AGPL}", rel))
    else:
        out.append(
            Finding(
                "warn",
                "rpm.license",
                "spec License is not AGPL-3.0-or-later",
                rel,
                line=_line_of(text, "License:"),
                fix=f"License:        {_AGPL}",
            )
        )

    url = re.search(r"^URL:\s*(\S+)", text, re.M)
    homepage = src.get("Homepage", "")
    if url and homepage and url.group(1).rstrip("/") != homepage.rstrip("/"):
        out.append(
            Finding(
                "warn",
                "rpm.URL",
                f"spec URL={url.group(1)!r} != debian Homepage={homepage!r}",
                rel,
                fix="Set URL: to the same Homepage as debian/control.",
            )
        )

    summary = re.search(r"^Summary:\s*(.+)$", text, re.M)
    desc = pkg.get("Description", "")
    deb_summary = desc.split("\n", 1)[0].strip() if desc else ""
    if summary and deb_summary and summary.group(1).strip() != deb_summary:
        out.append(
            Finding(
                "warn",
                "rpm.Summary",
                "spec Summary does not match debian Description first line",
                rel,
                line=_line_of(text, "Summary:"),
                fix=f"Summary:        {deb_summary}",
            )
        )

    if "meson" in text.lower() and "%configure" not in text:
        out.append(Finding("ok", "rpm.build", "spec uses Meson (not autotools)", rel))
    elif "%configure" in text or "autoreconf" in text:
        out.append(
            Finding(
                "error",
                "rpm.build",
                "spec still uses autotools; zephyr packages build with Meson",
                rel,
                fix="%build: meson setup build --prefix=%{_prefix} ... && meson compile -C build\n"
                "%install: meson install -C build --destdir=%{buildroot}",
            )
        )

    if makefile.is_file():
        if "zfr version" in mk:
            out.append(
                Finding("ok", "rpm.makefile.version", "Makefile uses `zfr version`", "rpm/Makefile")
            )
        else:
            out.append(
                Finding(
                    "warn",
                    "rpm.makefile.version",
                    "rpm/Makefile does not call `zfr version`",
                    "rpm/Makefile",
                    fix="VERSION := $(shell cd \"$(SRCDIR)\" && zfr version)\n"
                    "RPM_VERSION := $(shell cd \"$(SRCDIR)\" && zfr version -r)",
                )
            )
    else:
        out.append(
            Finding(
                "note",
                "rpm.makefile",
                "no rpm/Makefile convenience targets",
                "rpm/Makefile",
                fix="Copy bash/rpm/Makefile (srpm/rpm via zfr version).",
            )
        )

    if lang == "bash" and "bash-shlib" not in text:
        out.append(
            Finding(
                "error",
                "rpm.Requires.bash-shlib",
                "bash spec Requires missing bash-shlib",
                rel,
                fix="Requires:       bash-shlib  (same as debian Depends)",
            )
        )
    return out
