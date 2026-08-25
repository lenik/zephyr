# SPDX-License-Identifier: AGPL-3.0-or-later
"""RPM %files helpers for gettext .mo and locale man pages.

Meson installs translated mans under ``$mandir/<locale>/man1/`` and gettext
catalogs under ``$datadir/locale/*/LC_MESSAGES/*.mo``.  rpmbuild rejects those
as unpackaged unless ``%files`` lists matching globs — which breaks
``zfr release -fI`` after a successful Debian build.
"""
from __future__ import annotations

import re
from pathlib import Path

from .. import TEMPLATE_PUFF


def meson_text(root: Path) -> str:
    path = root / "meson.build"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def ships_gettext_mo(root: Path) -> bool:
    """True when the build is expected to install gettext ``.mo`` catalogs."""
    po = root / "po"
    if po.is_dir() and any(po.glob("*.po")):
        return True
    text = meson_text(root)
    if re.search(r"\bi18n\.gettext\s*\(", text):
        return True
    if re.search(r"\bgettext\s*\(\s*meson\.project_name", text):
        return True
    if re.search(r"subdir\(\s*['\"]po['\"]\s*\)", text) and (root / "po").is_dir():
        return True
    return False


def ships_locale_mans(root: Path) -> bool:
    """True when Meson installs man pages under ``$mandir/<locale>/man1/``."""
    text = meson_text(root)
    if re.search(r"\bman_i18n_langs\b|\bman_i18n\b", text):
        return True
    if re.search(r"mandir\s*/\s*(lang|locale)\b", text):
        return True
    # install_dir: get_option('mandir') / lang / 'man1'
    if re.search(r"get_option\(\s*['\"]mandir['\"]\s*\)\s*/\s*lang\b", text):
        return True
    if re.search(r"mandir\s*/\s*lang\b", text):
        return True
    docs = root / "docs"
    if docs.is_dir():
        for child in docs.iterdir():
            if child.is_dir() and any(child.glob("*.adoc")):
                return True
    return False


def man_command_stems(root: Path, name: str) -> list[str]:
    """Command stems that have (or will have) English man pages."""
    stems: list[str] = []
    docs = root / "docs"
    if docs.is_dir():
        for adoc in sorted(docs.glob("*.adoc")):
            if adoc.stem not in stems:
                stems.append(adoc.stem)
    text = meson_text(root)
    for m in re.finditer(r"output:\s*'([^']+\.[1-9][a-zA-Z]*)'", text):
        stem = Path(m.group(1)).name.rsplit(".", 1)[0]
        # Skip locale-suffixed outputs like zfr.zh_CN.1
        if "." in stem:
            continue
        if stem and stem not in stems:
            stems.append(stem)
    if not stems:
        stems = [name]
    return stems


def locale_man_lines(root: Path, name: str, puffs: list[str] | None = None) -> list[str]:
    """``%files`` globs for locale mans, one per command stem.

    Prefer stems that actually have ``docs/<lang>/*.adoc`` translations so we
    do not claim unpackaged locale mans for English-only pages.
    """
    if not ships_locale_mans(root):
        return []
    translated: set[str] = set()
    docs = root / "docs"
    if docs.is_dir():
        for child in docs.iterdir():
            if child.is_dir():
                for adoc in child.glob("*.adoc"):
                    translated.add(adoc.stem)
    if translated:
        if puffs:
            stems = [p for p in puffs if p in translated]
        else:
            stems = sorted(translated)
    else:
        stems = list(puffs) if puffs else man_command_stems(root, name)
    return [f"%{{_mandir}}/*/man1/{stem}.1*" for stem in stems]


def gettext_mo_line(root: Path, name: str) -> str | None:
    if not ships_gettext_mo(root):
        return None
    return f"%{{_datadir}}/locale/*/LC_MESSAGES/{name}.mo"


def _files_section_span(text: str) -> tuple[int, int] | None:
    m = re.search(r"(?m)^%files\b.*$", text)
    if not m:
        return None
    start = m.end()
    n = re.search(
        r"(?m)^%(files|changelog|package|prep|build|install|description|check)\b",
        text[start:],
    )
    end = start + n.start() if n else len(text)
    return start, end


def files_section_body(text: str) -> str:
    span = _files_section_span(text)
    if span is None:
        return ""
    return text[span[0] : span[1]]


def _is_i18n_files_line(line: str) -> bool:
    """Lines that must be present for Meson-installed paths release needs."""
    return (
        "/locale/*/LC_MESSAGES/" in line
        or "%{_mandir}/*/man1/" in line
        or "/setup/" in line
    )


def sync_rpm_files(text: str, *, expected: list[str]) -> tuple[str, list[str]]:
    """Rewrite or extend ``%files`` so release RPM packaging can succeed.

    Leftover ``some_puff1`` / template puff tokens force a full rewrite from
    *expected*.  Otherwise only missing gettext ``.mo`` / locale-man globs are
    appended (so custom package layouts are not flooded with guessed bindirs).
    """
    notes: list[str] = []
    span = _files_section_span(text)
    if span is None:
        return text, notes
    start, end = span
    body = text[start:end]
    if TEMPLATE_PUFF in body or "some_puff1" in body:
        new_body = "\n" + "\n".join(expected) + "\n"
        return text[:start] + new_body + text[end:], ["%files rewritten (template puff)"]
    missing = [
        line for line in expected if _is_i18n_files_line(line) and line not in body
    ]
    if not missing:
        return text, notes
    body = body.rstrip("\n") + "\n" + "\n".join(missing) + "\n"
    preview = ", ".join(missing[:4])
    if len(missing) > 4:
        preview += f", +{len(missing) - 4} more"
    notes.append(f"%files + {preview}")
    return text[:start] + body + text[end:], notes
