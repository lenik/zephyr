# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize engine helpers — version/path substitution and configure_file scripts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from ... import append_meson_list_entry, changelog_version, is_probably_text, iter_files, version_file_version
from ..util import *  # noqa: F403

if TYPE_CHECKING:
    from . import Ize

# Longest-first replacements for hardcoded FHS prefixes in scripts.
_PATH_SUBSTS: tuple[tuple[str, str], ...] = (
    ("/usr/local/share", "@DATADIR@"),
    ("/usr/share/locale", "@LOCALEDIR@"),
    ("/usr/local/libexec", "@LIBEXECDIR@"),
    ("/usr/libexec", "@LIBEXECDIR@"),
    ("/usr/local/lib", "@LIBDIR@"),
    ("/usr/lib", "@LIBDIR@"),
    ("/usr/local/bin", "@BINDIR@"),
    ("/usr/bin", "@BINDIR@"),
    ("/usr/local/sbin", "@SBINDIR@"),
    ("/usr/sbin", "@SBINDIR@"),
    ("/usr/share", "@DATADIR@"),
    ("/usr/local", "@PREFIX@"),
    ("/usr", "@PREFIX@"),
)

_ABS_PATH_RE = re.compile(
    r"(?<![/\w])(/usr(?:/local)?(?:/(?:share|libexec|lib|bin|sbin|include|etc)"
    r"(?:/[^/\s'\"`]+)*)?)"
)


def _has_path_placeholder(text: str) -> bool:
    return bool(
        re.search(
            r"@(?:PREFIX|DATADIR|BINDIR|LIBDIR|LIBEXECDIR|SBINDIR|LOCALEDIR|PKGDATADIR)@",
            text,
        )
    )


def _replace_paths(text: str) -> str:
    """Replace hardcoded FHS paths with @PLACEHOLDER@ (skip shebang lines)."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        if line.lstrip().startswith("#!"):
            out.append(line)
            continue
        new = line
        for old, repl in _PATH_SUBSTS:
            if old in new:
                new = new.replace(old, repl)
        out.append(new)
    return "".join(out)


def _needs_path_subst(text: str) -> bool:
    if _has_path_placeholder(text):
        return False
    for i, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("#!"):
            continue
        if _ABS_PATH_RE.search(line):
            return True
    return False


def _is_script_for_subst(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return False
    parts = Path(rel).parts
    if any(p.endswith("_lib") for p in parts[:-1]):
        return False
    if path.suffix in {".c", ".h", ".cpp", ".hpp", ".cc", ".hh"}:
        return False
    if rel.startswith("src/") and len(parts) == 2:
        return True
    return path.suffix in {".sh", ".bash", ".py", ".pl", ".rb"}


def subst_versions(ize: "Ize") -> None:
    """Replace hardcoded versions and install paths under src/ with placeholders."""
    ver = changelog_version(ize.root) or version_file_version(ize.root)
    tokens: set[str] = set()
    if ver and ver not in {"0.0.0"}:
        tokens = {ver, ver.lstrip("v")}
        if ver.startswith("v"):
            tokens.add(ver[1:])
        tokens = {t for t in tokens if t and t != "0.0.0"}
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
        new = text
        did_version = False
        did_path = False
        is_c = ize.lang in _C_FAMILY and path.suffix in {".c", ".h", ".cpp", ".hpp", ".cc"}
        is_script = _is_script_for_subst(path, ize.root)

        # --- version ---
        if tokens and "@VERSION@" not in new and "PROJECT_VERSION" not in new:
            for tok in sorted(tokens, key=len, reverse=True):
                if tok not in new:
                    continue
                if is_c:
                    cand = new.replace(f'"{tok}"', "PROJECT_VERSION")
                    if cand != new:
                        new = cand
                        did_version = True
                    if "PROJECT_VERSION" in new and '#include "config.h"' not in new:
                        new = '#include "config.h"\n' + new
                elif is_script:
                    cand = new.replace(tok, "@VERSION@")
                    if cand != new:
                        new = cand
                        did_version = True

        # --- paths (installable scripts only) ---
        if is_script and _needs_path_subst(new):
            replaced = _replace_paths(new)
            if replaced != new:
                new = replaced
                did_path = True

        if new == text:
            continue

        if is_c:
            detail = []
            if did_version:
                detail.append(f"PROJECT_VERSION instead of {ver}")
            ize.write_text(path, new, ", ".join(detail) or "config.h version")
            ensure_config_h(ize)
            continue

        if not is_script:
            continue

        dest = path.with_name(path.name + ".in")
        if dest.exists():
            continue
        rel_in = _rel(ize.root, dest)
        notes = []
        if did_version:
            notes.append("@VERSION@")
        if did_path:
            notes.append("@PREFIX@/@DATADIR@/…")
        ize.write_text(
            dest,
            new,
            f"{'/'.join(notes) or 'placeholders'} from {_rel(ize.root, path)}",
        )
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
    if "PROJECT_VERSION" in text and "configure_file" in text and "config_h" in text:
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


_IZE_CFG_SNIPPET = """
ize_cfg = configuration_data()
ize_cfg.set('PACKAGE', meson.project_name())
ize_cfg.set('VERSION', meson.project_version())
ize_cfg.set('PREFIX', get_option('prefix'))
ize_cfg.set('BINDIR', bindir)
ize_cfg.set('DATADIR', datadir)
ize_cfg.set('LIBDIR', prefix / get_option('libdir'))
ize_cfg.set('LIBEXECDIR', prefix / get_option('libexecdir'))
ize_cfg.set('SBINDIR', prefix / get_option('sbindir'))
ize_cfg.set('LOCALEDIR', prefix / get_option('localedir'))
ize_cfg.set('PKGDATADIR', datadir / meson.project_name())
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
    # Already has a full ize_cfg / app_scripts configure loop.
    if "ize_cfg" in text and "configure_file" in text and "ize_scripts" in text:
        # Ensure path keys exist when we added path placeholders.
        if "ize_cfg.set('PREFIX'" not in text and "ize_cfg.set(\"PREFIX\"" not in text:
            text2 = text.replace(
                "ize_cfg.set('VERSION', meson.project_version())",
                "ize_cfg.set('VERSION', meson.project_version())\n"
                "ize_cfg.set('PREFIX', get_option('prefix'))\n"
                "ize_cfg.set('BINDIR', bindir)\n"
                "ize_cfg.set('DATADIR', datadir)\n"
                "ize_cfg.set('LIBDIR', prefix / get_option('libdir'))\n"
                "ize_cfg.set('LIBEXECDIR', prefix / get_option('libexecdir'))\n"
                "ize_cfg.set('SBINDIR', prefix / get_option('sbindir'))\n"
                "ize_cfg.set('LOCALEDIR', prefix / get_option('localedir'))\n"
                "ize_cfg.set('PKGDATADIR', datadir / meson.project_name())",
                1,
            )
            if text2 != text:
                ize.write_text(meson, text2, "ize_cfg path placeholders")
        return
    if "foreach script : app_scripts" in text and "configure_file" in text:
        return
    # Ensure bindir/datadir/prefix exist (language templates usually define them).
    if "bindir" not in text or "datadir" not in text:
        preamble = (
            "\nprefix = get_option('prefix')\n"
            "bindir = prefix / get_option('bindir')\n"
            "datadir = prefix / get_option('datadir')\n"
        )
        if "fs = import('fs')" not in text:
            preamble = "\nfs = import('fs')\n" + preamble
        text = text.rstrip() + preamble
    quoted = ",\n    ".join(f"'{r}'" for r in rels)
    snippet = _IZE_CFG_SNIPPET.format(quoted=quoted)
    ize.write_text(
        meson,
        text.rstrip() + "\n" + snippet,
        "configure_file for @VERSION@/@PREFIX@ scripts",
    )
