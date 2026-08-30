# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize engine helpers — RPM spec/Makefile alignment."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from ... import pkgdatadir, template_dir
from .. import spec as _spec
from ..debian import (
    ensure_rpm_bash_shlib,
    ensure_rpm_noarch_nodebug,
    strip_rpm_substvars,
)
from ..rpm_files import _all_meson_texts, sync_rpm_files
from ..util import *  # noqa: F403

render_spec = _spec.render_spec

if TYPE_CHECKING:
    from . import Ize

def ensure_rpm_spec(ize: "Ize") -> None:
    makefile_dest = ize.root / "rpm" / "Makefile"
    if not makefile_dest.is_file():
        src = None
        try:
            cand = template_dir(ize.lang) / "rpm" / "Makefile"
            if cand.is_file():
                src = cand
        except SystemExit:
            src = None
        if src is None:
            cand = pkgdatadir() / "bash" / "rpm" / "Makefile"
            if cand.is_file():
                src = cand
        if src is None:
            here = Path(__file__).resolve()
            # zfr/src/zfr_lib → monorepo root (parent of zfr/)
            repo = (
                here.parents[3]
                if here.parent.name == "zfr_lib"
                else here.parents[2]
            )
            cand = repo / "bash" / "rpm" / "Makefile"
            if cand.is_file():
                src = cand
        if src is not None:
            ize.copy_file(src, makefile_dest, "rpm/Makefile")
    if makefile_dest.is_file():
        from ...packaging import migrate_rpm_makefile_topdir

        mk_text = makefile_dest.read_text(encoding="utf-8", errors="ignore")
        migrated = migrate_rpm_makefile_topdir(mk_text)
        if migrated is not None:
            ize.write_text(
                makefile_dest,
                migrated if migrated.endswith("\n") else migrated + "\n",
                "rpm/Makefile TOPDIR -> %_topdir ($HOME/rpmbuild)",
            )
    specs = _specs(ize.root)
    spec_path = ize.root / "rpm" / f"{ize.name}.spec"
    legacy = ize.root / "rpm" / "zephyr.spec"
    if not specs:
        dest = spec_path if ize.name != "zephyr" else legacy
        ize.write_text(
            dest,
            render_spec(ize.root, ize.lang, ize.name),
            "RPM spec from debian/control",
        )
    elif specs:
        text = specs[0].read_text(encoding="utf-8", errors="ignore")
        details: list[str] = []
        new = text
        if re.search(r"^Version:\s*[0-9]", new, re.M) and "%{version}" not in new:
            new = re.sub(r"^Version:\s*.*$", "Version:        %{version}", new, count=1, flags=re.M)
            if "%{!?version:" not in new:
                new = (
                    "%{!?version:%global version 0.0.0}\n"
                    "%{!?srcversion:%global srcversion %{version}}\n\n"
                    + new
                )
            details.append("dynamic Version")
        if "License:" in new and _AGPL not in new:
            new = re.sub(r"^License:\s*.*$", f"License:        {_AGPL}", new, count=1, flags=re.M)
            details.append("License AGPL")
        if "%configure" in new or "autoreconf" in new:
            details.append("left autotools %build (not auto-rewritten; see zfr lint)")
        arch_bins = bool(
            re.search(r"\bexecutable\s*\(", _all_meson_texts(ize.root))
        )
        # Script-only packages (no Meson executable()) need noarch +
        # %global debug_package %{nil}; otherwise rpmbuild emits an empty
        # debuginfo subpackage and fails (seen on pure-Python 2meson).
        _script_langs = {"bash", "python", "perl", "java", "ruby", "typescript"}
        if ize.lang == "bash":
            patched, changed = ensure_rpm_bash_shlib(new)
            if changed:
                new = patched
                details.append("Requires bash-shlib")
        if ize.lang in _script_langs or arch_bins:
            patched, changed = ensure_rpm_noarch_nodebug(
                new, arch_binaries=arch_bins
            )
            if changed:
                new = patched
                details.append(
                    "drop noarch (ELF)"
                    if arch_bins
                    else "noarch + no debuginfo"
                )
        patched, changed = strip_rpm_substvars(new)
        if changed:
            new = patched
            details.append("strip Debian substvars from Requires")
        expected = _spec_files(ize.root, ize.lang, ize.name)
        synced, file_notes = sync_rpm_files(new, expected=expected)
        if file_notes:
            new = synced
            details.extend(file_notes)
        if new != text:
            ize.write_text(specs[0], new, ", ".join(details) or "spec touch-up")
