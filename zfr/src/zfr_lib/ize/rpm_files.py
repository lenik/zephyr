# SPDX-License-Identifier: AGPL-3.0-or-later
"""RPM %files helpers aligned with what Meson actually installs.

Guessing bindir/completion/man from docs/*.adoc caused rpmbuild
"File not found" / "Installed (but unpackaged)" failures under
``zfr release -fI``.  Prefer parsing meson.build install rules.
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


def _all_meson_texts(root: Path) -> str:
    chunks = [meson_text(root)]
    for m in re.finditer(r"subdir\(\s*['\"]([^'\"]+)['\"]\s*\)", chunks[0]):
        sub = root / m.group(1) / "meson.build"
        if sub.is_file():
            try:
                chunks.append(sub.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    return "\n".join(chunks)


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
    if re.search(r"get_option\(\s*['\"]mandir['\"]\s*\)\s*/\s*lang\b", text):
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
        if "." in stem:
            continue
        if stem and stem not in stems:
            stems.append(stem)
    if not stems:
        stems = [name]
    return stems


def locale_man_lines(root: Path, name: str, puffs: list[str] | None = None) -> list[str]:
    """``%files`` globs for locale mans, one per command stem."""
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
        stems = [p for p in puffs if p in translated] if puffs else sorted(translated)
    else:
        stems = list(puffs) if puffs else man_command_stems(root, name)
    return [f"%{{_mandir}}/*/man1/{stem}.1*" for stem in stems]


def gettext_mo_line(root: Path, name: str) -> str | None:
    if not ships_gettext_mo(root):
        return None
    return f"%{{_datadir}}/locale/*/LC_MESSAGES/{name}.mo"



def _meson_call_blocks(text: str, func: str) -> list[str]:
    """Extract argument text of ``func(...)`` calls with nested-paren awareness."""
    out: list[str] = []
    token = func + "("
    i = 0
    while True:
        j = text.find(token, i)
        if j < 0:
            break
        start = j + len(token)
        depth = 1
        k = start
        while k < len(text) and depth:
            ch = text[k]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            k += 1
        out.append(text[start : k - 1])
        i = k
    return out

def meson_rpm_files(root: Path, name: str) -> list[str]:
    """``%files`` lines derived from Meson install rules (not docs guesses)."""
    text = _all_meson_texts(root)
    files: list[str] = []
    seen: set[str] = set()

    def add(line: str) -> None:
        if line and line not in seen:
            seen.add(line)
            files.append(line)

    # ---- bindir ----
    for block in _meson_call_blocks(text, "configure_file"):
        if not re.search(r"install\s*:\s*true", block):
            continue
        if "bindir" not in block:
            continue
        if not re.search(
            r"install_dir:\s*(?:get_option\(\s*['\"]bindir['\"]\s*\)|bindir)\s*[,)]",
            block,
        ):
            continue
        out = re.search(r"output:\s*'([^']+)'", block)
        if out:
            add(f"%{{_bindir}}/{Path(out.group(1)).name}")

    for m in re.finditer(
        r"install_data\s*\(\s*'([^']+)'\s*,\s*install_dir:\s*"
        r"(?:get_option\(\s*['\"]bindir['\"]\s*\)|bindir)\s*[,)]",
        text,
    ):
        add(f"%{{_bindir}}/{Path(m.group(1)).name}")

    for m in re.finditer(
        r"install_data\s*\(\s*\[([^\]]*)\]\s*,\s*install_dir:\s*"
        r"(?:get_option\(\s*['\"]bindir['\"]\s*\)|bindir)\s*[,)]",
        text,
        re.S,
    ):
        for nm in re.finditer(r"'([^']+)'", m.group(1)):
            add(f"%{{_bindir}}/{Path(nm.group(1)).name}")

    for block in _meson_call_blocks(text, "executable"):
        if not re.search(r"install\s*:\s*true", block):
            continue
        name_m = re.match(r"\s*'([^']+)'", block)
        if name_m:
            add(f"%{{_bindir}}/{name_m.group(1)}")

    # ---- bash-completion ----
    # bash-completion via bash_files = [...] + foreach rename stem
    if "bash-completion" in text:
        bm = re.search(r"bash_files\s*=\s*\[([^\]]*)\]", text, re.S)
        if bm and "foreach" in text and "rename" in text:
            for nm in re.finditer(r"'([^']+)'", bm.group(1)):
                add(f"%{{_datadir}}/bash-completion/completions/{Path(nm.group(1)).stem}")
        for m in re.finditer(
            r"install_data\s*\(\s*'([^']+)'\s*,\s*install_dir:\s*[^\n]*bash-completion[^\n]*",
            text,
        ):
            block = m.group(0)
            ren = re.search(r"rename:\s*'([^']+)'", block)
            if ren:
                add(f"%{{_datadir}}/bash-completion/completions/{ren.group(1)}")
            else:
                # installed basename kept (e.g. coolutils.sh)
                add(f"%{{_datadir}}/bash-completion/completions/{Path(m.group(1)).name}")
        # install_data([ 'a', 'b' ], install_dir: … bash-completion …)
        for m in re.finditer(
            r"install_data\s*\(\s*\[([^\]]*)\]\s*,\s*install_dir:\s*[^\n]*bash-completion[^\n]*",
            text,
            re.S,
        ):
            for nm in re.finditer(r"'([^']+)'", m.group(1)):
                add(f"%{{_datadir}}/bash-completion/completions/{Path(nm.group(1)).name}")
        # configure_file(… install_dir: … bash-completion …)
        for block in _meson_call_blocks(text, "configure_file"):
            if not re.search(r"install\s*:\s*true", block):
                continue
            if "bash-completion" not in block:
                continue
            out = re.search(r"output:\s*'([^']+)'", block)
            if out:
                add(f"%{{_datadir}}/bash-completion/completions/{Path(out.group(1)).name}")

    # ---- man pages ----

    def _add_man(man: str) -> None:
        man = Path(man).name
        # skip localized pages like foo.zh_CN.1
        if re.search(r"\.[a-z]{2}(?:_[A-Z]{2})?\.\d", man):
            return
        if not re.match(r".+\.[1-9][a-zA-Z]*$", man):
            return
        stem, sec = man.rsplit(".", 1)
        add(f"%{{_mandir}}/man{sec[0]}/{stem}.{sec}*")

    for block in _meson_call_blocks(text, "custom_target"):
        if not re.search(r"install\s*:\s*true", block):
            continue
        if "mandir" not in block and not re.search(r"\bman[1-9]\b", block):
            continue
        out = re.search(r"output:\s*'([^']+)'", block)
        if out:
            _add_man(out.group(1))

    # install_man('foo.5') / install_man([ 'a.1', 'b.5' ])
    for m in re.finditer(r"install_man\s*\(\s*'([^']+)'\s*\)", text):
        _add_man(m.group(1))
    for m in re.finditer(r"install_man\s*\(\s*\[([^\]]*)\]\s*\)", text, re.S):
        for nm in re.finditer(r"'([^']+)'", m.group(1)):
            _add_man(nm.group(1))

    # ---- bulk data dirs ----

    # Extra pkgdata / perl modules / shared data / headers
    if re.search(
        rf"install_dir:\s*[^\n]*datadir[^\n]*/\s*(?:meson\.project_name\(\)|'{re.escape(name)}')\s*[,)]",
        text,
    ):
        # Avoid counting setup-only installs as pkgdata.
        pkg_installs = [
            m.group(0)
            for m in re.finditer(r"install_dir:\s*[^\n]+", text)
            if "datadir" in m.group(0)
            and ("project_name" in m.group(0) or f"'{name}'" in m.group(0))
            and "setup" not in m.group(0)
            and "doc" not in m.group(0)
            and "bash-completion" not in m.group(0)
            and "bash-alias" not in m.group(0)
        ]
        if pkg_installs:
            add("%{_datadir}/%{name}/*")
    if re.search(r"install_dir:\s*[^\n]*perl5", text):
        add("%{_datadir}/perl5/*")

    # datadir / 'samples' | 'driver' | 'inc' | 'qlogconf' | …
    _skip_datadir_subs = {
        "setup",
        "doc",
        "bash-completion",
        "bash-alias",
        "man",
        "locale",
        "info",
        "applications",
        "icons",
        "metainfo",
        "pixmaps",
    }
    for m in re.finditer(
        r"install_dir:\s*(?:get_option\(\s*['\"]datadir['\"]\s*\)|datadir)"
        r"\s*/\s*'([^']+)'",
        text,
    ):
        sub = m.group(1).strip("/")
        top = sub.split("/")[0]
        if top in _skip_datadir_subs or sub == name:
            continue
        add(f"%{{_datadir}}/{sub}/*")

    if re.search(
        r"install_dir:\s*get_option\(\s*['\"]includedir['\"]\s*\)"
        r"|\binstall_headers\s*\(",
        text,
    ):
        add("%{_includedir}/*")

    if re.search(
        r"install_dir:\s*(?:get_option\(\s*['\"]sysconfdir['\"]\s*\)|sysconfdir)\s*[,)]",
        text,
    ):
        add("%{_sysconfdir}/*")

    if re.search(r"shlib\.d", text):
        add("%{_prefix}/lib/shlib.d/*")
    if "bash-alias" in text and "aliases" in text:
        add("%{_datadir}/bash-alias/aliases/*")
    if re.search(r"x11conf|x-alts", text):
        add("%{_datadir}/x11conf/*")

    if (
        (root / "postinst.in").is_file()
        or (root / "prerm.in").is_file()
        or re.search(r"['\"]setup['\"]\s*/\s*meson\.project_name", text)
    ):
        add("%{_datadir}/setup/%{name}/")

    mo = gettext_mo_line(root, name)
    if mo:
        add(mo)
    for line in locale_man_lines(root, name):
        add(line)

    add("%{_datadir}/doc/%{name}/")
    return files


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


def sync_rpm_files(text: str, *, expected: list[str]) -> tuple[str, list[str]]:
    """Rewrite ``%files`` to match *expected* (Meson install set)."""
    notes: list[str] = []
    if not expected:
        return text, notes
    span = _files_section_span(text)
    if span is None:
        return text, notes
    start, end = span
    body = text[start:end]
    current = [
        ln.strip()
        for ln in body.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if current == expected:
        return text, notes
    new_body = "\n" + "\n".join(expected) + "\n"
    why = (
        "template puff"
        if (TEMPLATE_PUFF in body or "some_puff1" in body)
        else "meson installs"
    )
    return text[:start] + new_body + text[end:], [f"%files synced ({why})"]
