# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize engine helpers — version substitution and configure_file scripts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from ... import append_meson_list_entry, changelog_version, is_probably_text, iter_files, version_file_version
from ..util import *  # noqa: F403

if TYPE_CHECKING:
    from . import Ize


def subst_versions(ize: "Ize") -> None:
    ver = changelog_version(ize.root) or version_file_version(ize.root)
    if not ver or ver in {"0.0.0"}:
        return
    tokens = {ver, ver.lstrip("v")}
    if ver.startswith("v"):
        tokens.add(ver[1:])
    src_root = ize.root / "src"
    if not src_root.is_dir():
        return
    converted: list[Path] = []
    for path in list(iter_files(src_root)):
        if path.suffix == ".in" or path.name.endswith(".in"):
            continue
        if not is_probably_text(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "@VERSION@" in text:
            continue
        new = text
        for tok in sorted(tokens, key=len, reverse=True):
            if not tok or tok == "0.0.0":
                continue
            if tok not in new:
                continue
            if ize.lang in _C_FAMILY and path.suffix in {".c", ".h", ".cpp", ".hpp", ".cc"}:
                new = new.replace(f'"{tok}"', "PROJECT_VERSION")
                new = re.sub(
                    rf"#define\s+VERSION\s+PROJECT_VERSION",
                    "#define VERSION PROJECT_VERSION",
                    new,
                )
                if "PROJECT_VERSION" in new and '#include "config.h"' not in new:
                    new = '#include "config.h"\n' + new
            else:
                new = new.replace(tok, "@VERSION@")
        if new == text:
            continue
        if ize.lang in _C_FAMILY and path.suffix in {".c", ".h", ".cpp", ".hpp", ".cc"}:
            ize.write_text(path, new, f"use PROJECT_VERSION instead of {ver}")
            ensure_config_h(ize)
            continue
        # scripts → .in
        dest = path.with_name(path.name + ".in")
        if dest.exists():
            continue
        rel_in = _rel(ize.root, dest)
        ize.write_text(dest, new, f"@VERSION@ subst from {_rel(ize.root, path)}")
        converted.append(dest)
        if not ize.dry_run:
            path.unlink()
        ize.note("convert", _rel(ize.root, path), f"replaced by {rel_in}")
    if converted:
        ensure_ize_scripts(ize, converted)

def ensure_config_h(ize: "Ize") -> None:
    meson = ize.root / "meson.build"
    if not meson.is_file():
        return
    text = meson.read_text(encoding="utf-8")
    if "PROJECT_VERSION" in text and "configure_file" in text:
        return
    snippet = """
config_h = configuration_data()
config_h.set_quoted('PROJECT_VERSION', meson.project_version())
config_h.set_quoted('PROJECT_AUTHOR', project_author)
config_h.set_quoted('PROJECT_EMAIL', project_email)
config_h.set('PROJECT_YEAR', project_year)
configure_file(
output: 'config.h',
configuration: config_h,
)
"""
    if "config_h" not in text:
        ize.write_text(
            meson,
            text.rstrip() + "\n" + snippet,
            "configure_file config.h with PROJECT_VERSION",
        )

def ensure_ize_scripts(ize: "Ize", ins: list[Path]) -> None:
    meson = ize.root / "meson.build"
    if not meson.is_file():
        return
    rels = []
    for p in ins:
        rel = _rel(ize.root, p).replace("\\", "/")
        rels.append(rel)
        if not ize.dry_run:
            append_meson_list_entry(meson, "app_scripts", rel)
            append_meson_list_entry(meson, "ize_scripts", rel)
    text = meson.read_text(encoding="utf-8")
    if "ize_scripts" in text and "configure_file" in text and "ize_cfg" in text:
        return
    if "foreach script : app_scripts" in text and "configure_file" in text:
        return
    quoted = ",\n    ".join(f"'{r}'" for r in rels)
    snippet = f"""
ize_cfg = configuration_data()
ize_cfg.set('PACKAGE', meson.project_name())
ize_cfg.set('VERSION', meson.project_version())
ize_scripts = [
{quoted},
]
foreach script : ize_scripts
name = fs.stem(script.split('/')[-1])
configured = configure_file(
    input: script,
    output: name,
    configuration: ize_cfg,
)
install_data(configured, install_dir: bindir, install_mode: 'rwxr-xr-x')
endforeach
"""
    ize.write_text(meson, text.rstrip() + "\n" + snippet, "configure_file for @VERSION@ scripts")
