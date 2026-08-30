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

from ..lang import spec_extra_files as _lang_spec_extra_files
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
from ..lint.util import _control, _role, _specs
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
    "autom4te.cache",
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
    rule: str = ""


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _project_call_end(text: str) -> int | None:
    """Index just past the closing ')' of the first project(...) call.

    Skips parentheses inside Meson string literals (including triple quotes)
    so nested run_command() / shell snippets do not truncate the span.
    """
    m = re.search(r"project\s*\(", text)
    if not m:
        return None
    i = m.end()
    depth = 1
    n = len(text)
    while i < n and depth:
        ch = text[i]
        if ch in ("'", '"'):
            quote = ch
            # Triple-quoted string?
            if i + 2 < n and text[i : i + 3] == quote * 3:
                i += 3
                while i + 2 < n and text[i : i + 3] != quote * 3:
                    i += 1
                i = min(i + 3, n)
                continue
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
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


def bump_patch_version(ver: str) -> str:
    """Bump the patch (third) field of a Debian upstream version.

    ``1.2.3`` → ``1.2.4``; ``1.2`` → ``1.2.1``; epochs and ``-revision``
    are preserved (``1:1.0.0-2`` → ``1:1.0.1-2``).
    """
    ver = (ver or "").strip().lstrip("v")
    if not ver:
        return "0.0.1"
    epoch = ""
    if ":" in ver:
        epoch, ver = ver.split(":", 1)
        epoch = f"{epoch}:"
    deb_rev = ""
    if "-" in ver:
        ver, rev = ver.rsplit("-", 1)
        deb_rev = f"-{rev}"
    parts = ver.split(".")
    while len(parts) < 3:
        parts.append("0")
    # Bump the third component (patch); zero any further numeric tails.
    idx = 2
    if not parts[idx].isdigit():
        for i in range(len(parts) - 1, -1, -1):
            if parts[i].isdigit():
                idx = i
                break
        else:
            parts.append("1")
            return epoch + ".".join(parts) + deb_rev
    parts[idx] = str(int(parts[idx]) + 1)
    for j in range(idx + 1, len(parts)):
        if parts[j].isdigit():
            parts[j] = "0"
    return epoch + ".".join(parts) + deb_rev


def changelog_distribution(root: Path) -> str:
    """Distribution from the top debian/changelog stanza, or the create default."""
    path = root / "debian" / "changelog"
    if path.is_file():
        first = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
        if first:
            m = re.match(r"\S+\s+\([^)]+\)\s+(\S+);", first[0])
            if m:
                return m.group(1)
    return DEFAULT_DISTRIBUTION


_CHANGELOG_TRAILER_RE = re.compile(
    r"^ -- (.+?) <([^>]+)>  .+$",
    re.M,
)


def changelog_author(root: Path) -> tuple[str, str] | None:
    """Author of the latest debian/changelog stanza (``Name``, ``email``)."""
    path = root / "debian" / "changelog"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = _CHANGELOG_TRAILER_RE.search(text)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


def parse_author_spec(spec: str) -> tuple[str, str | None]:
    """Parse ``Name <email>`` or bare ``Name`` into ``(name, email|None)``."""
    spec = spec.strip()
    m = re.match(r"^(.+?)\s*<([^>]+)>\s*$", spec)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return spec, None


def resolve_changelog_author(
    root: Path,
    *,
    author_override: str | None = None,
) -> tuple[str, str]:
    """Changelog signer: ``--author``, else previous stanza, else Maintainer."""
    if author_override:
        name, email = parse_author_spec(author_override)
        if email:
            return name, email
        prev = changelog_author(root)
        if prev:
            return name, prev[1]
        _, maint_email = _maintainer(root)
        return name, maint_email
    prev = changelog_author(root)
    if prev:
        return prev
    return _maintainer(root)


def prepend_debian_changelog(
    root: Path,
    *,
    package: str,
    version: str,
    bullets: list[str],
    distribution: str | None = None,
    author: str | None = None,
    email: str | None = None,
    author_override: str | None = None,
) -> None:
    """Insert a new top stanza in debian/changelog and sync VERSION."""
    from email.utils import formatdate

    if author is None or email is None:
        a, e = resolve_changelog_author(root, author_override=author_override)
        author = author or a
        email = email or e
    dist = distribution or changelog_distribution(root)
    ver = version.lstrip("v")
    stamp = formatdate(localtime=True)
    if not bullets:
        bullets = ["zfr ize"]
    body = "\n".join(f"  * {b}" for b in bullets)
    stanza = (
        f"{package} ({ver}) {dist}; urgency=medium\n"
        f"\n"
        f"{body}\n"
        f"\n"
        f" -- {author} <{email}>  {stamp}\n"
        f"\n"
    )
    path = root / "debian" / "changelog"
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(stanza + old, encoding="utf-8")
    (root / "VERSION").write_text(f"{ver}\n", encoding="utf-8")


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
        # Drop Debian substvars glued on the same token (e.g. "bash-shlib ${misc:Depends}").
        item = re.sub(r"\$\{[^}]+\}", "", item).strip()
        if not item or item.startswith("${") or item.startswith("debhelper"):
            continue
        # Keep first package token only if spaces remain after stripping substvars.
        item = item.split()[0]
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
    """RPM %files: prefer Meson install rules; fall back to puff guesses."""
    from .rpm_files import meson_rpm_files

    meson_files = meson_rpm_files(root, name)
    # Meson-derived list is authoritative when it found any install (bindir/man/…).
    meson_authoritative = any(
        x.startswith("%{_bindir}/")
        or x.startswith("%{_mandir}/")
        or "/shlib.d/" in x
        or "/bash-completion/" in x
        for x in meson_files
    )
    if meson_authoritative:
        files = list(meson_files)
    else:
        from .rpm_files import gettext_mo_line, locale_man_lines

        puffs = _puff_names(root) or [name]
        files = []
        for puff in puffs:
            files.append(f"%{{_bindir}}/{puff}")
            files.append(f"%{{_datadir}}/bash-completion/completions/{puff}")
            files.append(f"%{{_mandir}}/man1/{puff}.1*")
            files.extend(locale_man_lines(root, name, [puff]))
        mo = gettext_mo_line(root, name)
        if mo:
            files.append(mo)
        meson_txt = ""
        mb = root / "meson.build"
        if mb.is_file():
            meson_txt = mb.read_text(encoding="utf-8", errors="ignore")
        if re.search(
            r"['\"]setup['\"]\s*/\s*meson\.project_name|datadir\s*/\s*['\"]setup['\"]",
            meson_txt,
        ):
            files.append("%{_datadir}/setup/%{name}/")
        files.append("%{_datadir}/doc/%{name}/")
        # Lang template extras (e.g. Java ``%{_datadir}/%{name}/``) only when
        # Meson did not already define the install set — otherwise they invent
        # empty dirs that rpmbuild rejects as "Directory not found".
        extras = _lang_spec_extra_files(lang, puffs)
        insert_after_bindir: list[str] = []
        append_before_doc: list[str] = []
        for extra in extras:
            if extra.startswith("%{_infodir}/"):
                append_before_doc.append(extra)
            else:
                insert_after_bindir.append(extra)
        if insert_after_bindir:
            idx = next(
                (i for i, f in enumerate(files) if f.startswith("%{_bindir}/")),
                -1,
            )
            if idx >= 0:
                files[idx + 1 : idx + 1] = insert_after_bindir
            else:
                files[0:0] = insert_after_bindir
        files = [f for f in files if f != "%{_datadir}/doc/%{name}/"]
        files.extend(append_before_doc)
        files.append("%{_datadir}/doc/%{name}/")

    # Keep doc last.
    files = [f for f in files if f != "%{_datadir}/doc/%{name}/"]
    files.append("%{_datadir}/doc/%{name}/")

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
