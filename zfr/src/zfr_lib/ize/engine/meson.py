# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize engine helpers — Meson and man-page patching."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ... import iter_files
from .. import man as _man
from ..util import *  # noqa: F403

convert_man_file = _man.convert_man_file
_man_target = _man._man_target
strip_install_man_paths = _man.strip_install_man_paths
discover_man_stems = _man.discover_man_stems
strip_help2man_blocks = _man.strip_help2man_blocks

if TYPE_CHECKING:
    from . import Ize


def patch_meson_build(ize: "Ize") -> None:
    path = ize.root / "meson.build"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    orig = text
    details: list[str] = []

    if _GIT_DESCRIBE_RE.search(text):
        text = _GIT_DESCRIBE_RE.sub(lambda _m: VERSION_SHELL, text, count=1)
        details.append("version via zfr version")
    elif "zfr version" not in text:
        proj_end = _project_call_end(text)
        proj = text[text.find("project(") : proj_end] if proj_end else ""
        ver_lit = re.search(r"version\s*:\s*'[^']+'", proj or text)
        if ver_lit:
            text = re.sub(
                r"version\s*:\s*'[^']+'",
                lambda _m: "version: " + VERSION_RUN,
                text,
                count=1,
            )
            details.append("replace hardcoded project version")
        elif proj_end and not re.search(r"version\s*:", proj):
            def _inject(m: re.Match[str]) -> str:
                return m.group(0) + "\n    version: " + VERSION_RUN + ","
            text2, n = re.subn(
                r"project\s*\(\s*['\"][^'\"]+['\"]\s*,?",
                _inject,
                text,
                count=1,
            )
            if n:
                text = text2
                details.append("inject zfr version")

    end = _project_call_end(text)
    if end is not None:
        insert_at = end
        proj_span = text[text.find("project(") : end]
        if not re.search(r"license\s*:", proj_span) and _AGPL not in proj_span:
            # Insert before closing paren; ensure a comma after the previous arg.
            before = text[: end - 1].rstrip()
            sep = "" if before.endswith(",") else ","
            extra_license = f"{sep}\n    license: '{_AGPL}'"
            text = before + extra_license + text[end - 1 :]
            insert_at = len(before) + len(extra_license) + 1  # past ')'
            details.append("license AGPL-3.0-or-later")
            end = insert_at
        after = text[end:]
        author, email = _maintainer(ize.root)
        block = ""
        if "project_author" not in text:
            block += f"\nproject_author = '{author}'\n"
        if "project_email" not in text:
            block += f"project_email = '{email}'\n"
        if "project_year" not in text:
            block += "project_year = 2026\n"
        if block:
            text = text[:end] + block + after
            details.append("project_author/email/year")

    if "asciidoctor" not in text:
        text += "\nasciidoctor = find_program('asciidoctor', required: true)\n"
        details.append("find_program asciidoctor")

    if "pkgdocdir" not in text:
        bits: list[str] = []
        if not re.search(r"\bprefix\s*=", text):
            bits.append("prefix = get_option('prefix')")
        if not re.search(r"\bbindir\s*=", text):
            bits.append("bindir = prefix / get_option('bindir')")
        if not re.search(r"\bdatadir\s*=", text):
            bits.append("datadir = prefix / get_option('datadir')")
        if not re.search(r"\bmandir\s*=", text):
            bits.append("mandir = prefix / get_option('mandir')")
        bits.append("pkgdocdir = datadir / 'doc' / meson.project_name()")
        text += "\n" + "\n".join(bits) + "\n"
        details.append("prefix/bindir/datadir/mandir/pkgdocdir")

    if "fs = import('fs')" not in text and "import('fs')" not in text:
        text += "\nfs = import('fs')\n"
        details.append("import fs")

    docs = [
        p
        for p in (
            list((ize.root / "docs").glob("*.adoc"))
            if (ize.root / "docs").is_dir()
            else []
        )
    ]
    for adoc in docs:
        needle = f"docs/{adoc.name}"
        if needle not in text and f"'{adoc.stem}-man'" not in text:
            section = "1"
            try:
                first = adoc.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
                m = re.match(r"^=\s+\S+\((\d+[a-zA-Z]*)\)", first)
                if m:
                    section = m.group(1)
            except (OSError, IndexError):
                pass
            text += _man_target(adoc.stem, section)
            details.append(f"man target {adoc.stem}")

    if not re.search(r"run_target\s*\(\s*['\"]look['\"]", text):
        text += LOOK_TARGET
        details.append("run_target look")

    license_files = [
        n for n in ("LICENSE", "README.md", "README-zh.md") if (ize.root / n).is_file()
    ]
    if license_files and "install_dir: pkgdocdir" not in text:
        quoted = ",\n        ".join(f"'{n}'" for n in license_files)
        text += (
            "\ninstall_data(\n    [\n        "
            + quoted
            + ",\n    ],\n    install_dir: pkgdocdir,\n)\n"
        )
        details.append("install LICENSE/README")

    completions = sorted(ize.root.glob("*.bash"))
    comp_dir = ize.root / "completions"
    if comp_dir.is_dir():
        completions.extend(
            sorted(
                p
                for p in comp_dir.glob("*.bash")
                if p.is_file() and not p.name.startswith(".")
            )
        )
    if completions:
        # Prefer install_data of each path; rename to command stem.
        entries: list[str] = []
        for p in completions:
            rel = p.relative_to(ize.root).as_posix()
            entries.append(f"    '{rel}'")
        names = ",\n".join(entries)
        block = f"""
bash_files = [
{names},
]

foreach file : bash_files
name = fs.stem(file)
install_data(
    file,
    install_dir: datadir / 'bash-completion' / 'completions',
    rename: name,
)
endforeach
"""
        if "bash-completion" not in text:
            if "fs = import('fs')" not in text and "fs=import('fs')" not in text:
                # fs.stem needs the fs module
                text += "\nfs = import('fs')\n"
            text += block
            details.append("install bash-completion")
        else:
            new_text, nsub = re.subn(
                r"bash_files\s*=\s*\[[^\]]*\]",
                "bash_files = [\n" + names + ",\n]",
                text,
                count=1,
                flags=re.S,
            )
            if nsub and new_text != text:
                text = new_text
                details.append("refresh bash-completion list")

    if text != orig:
        ize.write_text(path, text if text.endswith("\n") else text + "\n", ", ".join(details))

def convert_manpages(ize: "Ize") -> None:
    docs = ize.root / "docs"
    man_re = re.compile(r"^(?P<stem>.+)\.(?P<section>[1-9][a-zA-Z]*)(?:\.in)?$")
    for path in list(iter_files(ize.root)):
        m = man_re.match(path.name)
        if not m:
            continue
        rel_parts = path.resolve().relative_to(ize.root.resolve()).parts
        if any(part in SKIP_MAN_PARTS for part in rel_parts):
            continue
        stem = m.group("stem")
        section = m.group("section")
        dest = docs / f"{stem}.adoc"
        if dest.is_file():
            if ize.verbose:
                ize.note("skip", _rel(ize.root, dest), "adoc already exists")
            continue
        try:
            adoc = convert_man_file(path, stem, section=section)
        except OSError as e:
            ize.note("skip", _rel(ize.root, path), f"convert failed: {e}")
            continue
        if len(adoc.strip()) < 40:
            ize.note("skip", _rel(ize.root, path), "conversion too small")
            continue
        ize.write_text(dest, adoc, f"from {_rel(ize.root, path)}", kind="convert")
        rel_src = _rel(ize.root, path)
        if path.parent in (ize.root, ize.root / "docs", ize.root / "man"):
            ize.note("convert", rel_src, "removed groff source; meson generates manpage")
            if not ize.dry_run:
                path.unlink(missing_ok=True)
        meson = ize.root / "meson.build"
        if meson.is_file():
            text = meson.read_text(encoding="utf-8")
            new = strip_install_man_paths(
                text, {rel_src, path.name, f"{stem}.{section}"}
            )
            if new != text:
                ize.write_text(meson, new, f"drop groff {rel_src} from install_man")

def patch_meson_man_targets(ize: "Ize") -> None:
    path = ize.root / "meson.build"
    if not path.is_file() or not (ize.root / "docs").is_dir():
        return
    text = path.read_text(encoding="utf-8")
    orig = text
    details: list[str] = []
    if "asciidoctor" not in text:
        text += "\nasciidoctor = find_program('asciidoctor', required: true)\n"
        details.append("find_program asciidoctor")
    if "mandir" not in text:
        text += (
            "\nprefix = get_option('prefix')\n"
            "mandir = prefix / get_option('mandir')\n"
        )
        details.append("mandir")
    # Strip leftover install_man(.../*.adoc) from a prior ize run.
    cleaned = strip_install_man_paths(text, set())
    if cleaned != text:
        text = cleaned
        details.append("remove AsciiDoc paths from install_man")
    for adoc in sorted((ize.root / "docs").glob("*.adoc")):
        if f"'{adoc.stem}-man'" in text or f'"{adoc.stem}-man"' in text:
            continue
        section = "1"
        try:
            first = adoc.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
            m = re.match(r"^=\s+\S+\((\d+[a-zA-Z]*)\)", first)
            if m:
                section = m.group(1)
        except (OSError, IndexError):
            pass
        text += _man_target(adoc.stem, section)
        details.append(f"man target {adoc.stem}")
    if text != orig:
        ize.write_text(path, text if text.endswith("\n") else text + "\n", ", ".join(details))
