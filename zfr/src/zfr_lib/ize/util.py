# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr ize — bring an existing project up to current zephyr style."""

from __future__ import annotations

import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .. import (
    LANGS,
    SKIP_DIR_NAMES,
    TEMPLATE_PUFF,
    _is_zfr_meta_repo,
    append_meson_list_entry,
    changelog_version,
    copy_renamed_file,
    detect_lang,
    find_project_dir,
    instantiation_pairs,
    is_probably_text,
    iter_files,
    pkgdatadir,
    template_dir,
    version_file_version,
)
from ..create import (
    DEFAULT_AUTHOR,
    DEFAULT_DISTRIBUTION,
    DEFAULT_EMAIL,
    DEFAULT_INIT_VERSION,
    _install_githooks,
    _write_debian_changelog,
)
from ..csr import Csr
from ..lint import _control, _role, _specs
from ..packaging import _meson_project_fields

_AGPL = "AGPL-3.0-or-later"

VERSION_SHELL = """\
        v=$(
            command -v zfr >/dev/null 2>&1 && zfr version 2>/dev/null || true
        )
        if [ -z "$v" ] && [ -f VERSION ]; then
            v=$(head -n1 VERSION | tr -d '\\r')
            v=${v#v}
        fi
        if [ -z "$v" ]; then
            v="0.0.0" # FIXED TO 0.0.0, DO NOT MODIFY
        fi
        printf '%s' "$v"\
"""

# Meson file body (tr -d '\\r' is a literal backslash-r for the shell).
VERSION_RUN = """\
run_command(
        'sh',
        '-c', '''
        v=$(
            command -v zfr >/dev/null 2>&1 && zfr version 2>/dev/null || true
        )
        if [ -z "$v" ] && [ -f VERSION ]; then
            v=$(head -n1 VERSION | tr -d '\\r')
            v=${v#v}
        fi
        if [ -z "$v" ]; then
            v="0.0.0" # FIXED TO 0.0.0, DO NOT MODIFY
        fi
        printf '%s' "$v"
        ''',
        check: false,
    ).stdout().strip()\
"""

LOOK_TARGET = """
run_target(
    'look',
    command: [
        'bash',
        '-euc', '''
            tmpdir=$(mktemp -d)
            DESTDIR=$tmpdir meson install -C "@BUILD_ROOT@"
            tree "$tmpdir"
            rm -fr "$tmpdir"
        ''',
    ],
)
"""

SCAFFOLD = (
    "LICENSE",
    "README.md",
    "README-zh.md",
    "debian/control",
    "debian/copyright",
    "debian/rules",
    "debian/source/format",
    "rpm/Makefile",
)

SKIP_MAN_PARTS = SKIP_DIR_NAMES | {
    "debian",
    "po",
    "rpm",
    "githooks",
}

_GIT_DESCRIBE_RE = re.compile(
    r"v=\$\(git describe --tags --always --dirty 2>/dev/null \|\| true\)"
    r".*?printf '%s' \"\$v\"",
    re.S,
)

_C_FAMILY = {"c", "clib", "cpp", "cpplib"}


@dataclass
class Change:
    kind: str  # add, update, convert, skip
    path: str
    detail: str


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _project_call_end(text: str) -> int | None:
    m = re.search(r"project\s*\(", text)
    if not m:
        return None
    i = m.end()
    depth = 1
    while i < len(text) and depth:
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
        i += 1
    return i if depth == 0 else None


def _maintainer(root: Path) -> tuple[str, str]:
    src, _, _ = _control(root)
    raw = src.get("Maintainer") or ""
    m = re.match(r"(.+?)\s*<([^>]+)>", raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return DEFAULT_AUTHOR, DEFAULT_EMAIL


def _homepage(root: Path) -> str:
    src, _, _ = _control(root)
    return src.get("Homepage") or "https://github.com/lenik/zephyr"


def _split_deps(raw: str) -> list[str]:
    if not raw:
        return []
    out: list[str] = []
    for chunk in raw.replace("\n", " ").split(","):
        item = chunk.strip()
        if not item:
            continue
        item = item.split("|", 1)[0].strip()
        item = re.sub(r"\s*\([^)]*\)", "", item).strip()
        if item.startswith("${") or item.startswith("debhelper"):
            continue
        out.append(item)
    return out


def _puff_names(root: Path) -> list[str]:
    names: list[str] = []
    docs = root / "docs"
    if docs.is_dir():
        for p in sorted(docs.glob("*.adoc")):
            if p.stem not in names:
                names.append(p.stem)
    src = root / "src"
    if src.is_dir():
        for p in sorted(src.iterdir()):
            if not p.is_file():
                continue
            stem = p.name
            if stem.endswith(".in"):
                stem = Path(stem[:-3]).stem
            else:
                stem = p.stem
            if stem and stem not in names and not stem.startswith("common"):
                if TEMPLATE_PUFF in stem or re.match(r"^[a-zA-Z][\w-]*$", stem):
                    names.append(stem)
    for p in sorted(root.glob("*.bash")):
        if p.stem not in names:
            names.append(p.stem)
    return names


def _spec_files(root: Path, lang: str, name: str) -> list[str]:
    puffs = _puff_names(root) or [TEMPLATE_PUFF]
    files: list[str] = []
    for puff in puffs:
        files.append(f"%{{_bindir}}/{puff}")
        files.append(f"%{{_datadir}}/bash-completion/completions/{puff}")
        files.append(f"%{{_mandir}}/man1/{puff}.1*")
    if lang == "python":
        files.insert(1, "%{_bindir}/common_lib.py")
    if lang == "java":
        files.insert(1, "%{_datadir}/%{name}/")
    if lang == "typescript":
        files.insert(1, "%{_datadir}/%{name}/")
        files.append("%{_infodir}/%s.info*" % (puffs[0] if puffs else "zephyr"))
    if lang in ("clib", "cpplib"):
        files[1:1] = [
            "%{_libdir}/lib%s.so*" % name,
            "%{_libdir}/pkgconfig/%s.pc" % name,
            "%{_libdir}/pkgconfig/%s-static.pc" % name,
            "%{_includedir}/%s/" % name,
        ]
    files.append("%{_datadir}/doc/%{name}/")
    if (root / "po").is_dir():
        files.append("%{_datadir}/locale/*/LC_MESSAGES/%s.mo" % name)
    # unique, keep order
    seen: set[str] = set()
    out: list[str] = []
    for f in files:
        if f in seen:
            continue
        seen.add(f)
        out.append(f)
    return out


# import * must re-export underscore helpers used by spec/man/engine.
__all__ = [n for n in globals() if not n.startswith("__")]
