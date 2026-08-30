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


def meson_project_name(root: Path, fallback: str = "") -> str:
    """Meson ``project('name', …)`` — drives install paths like share/<name>/."""
    text = meson_text(root)
    m = re.search(r"project\s*\(\s*['\"]([^'\"]+)['\"]", text)
    if m:
        return m.group(1)
    return fallback


def gettext_domain(root: Path, name: str) -> str:
    """Return the gettext domain Meson installs (``.mo`` basename).

    Prefer ``i18n.gettext('domain', …)`` / ``--domain`` over guessing from
    the RPM name alone (zephyr package uses domain ``zephyr``).
    """
    text = _all_meson_texts(root)
    m = re.search(
        r"i18n\.gettext\s*\(\s*['\"]([^'\"]+)['\"]",
        text,
    )
    if m:
        return m.group(1)
    m = re.search(r"['\"]--domain['\"]\s*,\s*['\"]([^'\"]+)['\"]", text)
    if m:
        return m.group(1)
    m = re.search(r"--domain['\"]?\s*,\s*['\"]([^'\"]+)['\"]", text)
    if m:
        return m.group(1)
    return name


def gettext_mo_line(root: Path, name: str) -> str | None:
    if not ships_gettext_mo(root):
        return None
    domain = gettext_domain(root, name)
    return f"%{{_datadir}}/locale/*/LC_MESSAGES/{domain}.mo"



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

    # foreach name : wrapper_names / ['a','b'] + configure_file(output: name → bindir)
    # (zfr installs PATH wrappers this way; output is a Meson variable, not a string)
    for m in re.finditer(
        r"foreach\s+(\w+)\s*:\s*(\w+|\[)(.*?)\bendforeach\b",
        text,
        re.S,
    ):
        var, head, body = m.group(1), m.group(2), m.group(3)
        if "configure_file" not in body:
            continue
        if not re.search(r"install\s*:\s*true", body):
            continue
        if not re.search(
            r"install_dir:\s*(?:get_option\(\s*['\"]bindir['\"]\s*\)|bindir)\s*[,)]",
            body,
        ):
            continue
        if not re.search(rf"output:\s*{re.escape(var)}\s*[,)]", body):
            continue
        names: list[str] = []
        if head == "[":
            # foreach x : [ 'a', 'b' ] — items are in body before first newline/configure
            bracket = re.match(r"([^\]]*)\]", body)
            if bracket:
                names = re.findall(r"'([^']+)'", bracket.group(1))
        else:
            # foreach x : wrapper_names
            list_m = re.search(
                rf"{re.escape(head)}\s*=\s*\[([^\]]*)\]",
                text,
                re.S,
            )
            if list_m:
                names = re.findall(r"'([^']+)'", list_m.group(1))
        for nm in names:
            add(f"%{{_bindir}}/{nm}")

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

    # custom_target(..., install: true, install_dir: bindir) — e.g. Python CLIs
    for block in _meson_call_blocks(text, "custom_target"):
        if not re.search(r"install\s*:\s*true", block):
            continue
        if not re.search(
            r"install_dir:\s*(?:get_option\(\s*['\"]bindir['\"]\s*\)|bindir)\s*[,)]",
            block,
        ):
            continue
        out = re.search(r"output:\s*'([^']+)'", block)
        if out:
            add(f"%{{_bindir}}/{Path(out.group(1)).name}")

    # install_subdir('src/pkg', install_dir: bindir) → %{_bindir}/pkg/
    # (2meson ships its library next to the CLI under bindir)
    for block in _meson_call_blocks(text, "install_subdir"):
        if not re.search(
            r"install_dir:\s*(?:get_option\(\s*['\"]bindir['\"]\s*\)|bindir)\s*[,)]",
            block,
        ):
            continue
        src = re.match(r"\s*'([^']+)'", block)
        if not src:
            continue
        dirname = Path(src.group(1)).name
        if dirname and dirname not in {".", ".."}:
            add(f"%{{_bindir}}/{dirname}/")

    # ---- bash-completion ----
    # bash-completion via bash_files = [...] + foreach rename stem
    if "bash-completion" in text:
        bm = re.search(r"bash_files\s*=\s*\[([^\]]*)\]", text, re.S)
        if bm and "foreach" in text and "rename" in text:
            for nm in re.finditer(r"'([^']+)'", bm.group(1)):
                add(f"%{{_datadir}}/bash-completion/completions/{Path(nm.group(1)).stem}")
        # foreach name : ['a','b',…] / install_data(..., rename: name)
        for m in re.finditer(
            r"foreach\s+(\w+)\s*:\s*\[([^\]]*)\](.*?)endforeach",
            text,
            re.S,
        ):
            var, items, body = m.group(1), m.group(2), m.group(3)
            if "bash-completion" not in body:
                continue
            if not re.search(rf"rename\s*:\s*{re.escape(var)}\s*[,)]", body):
                continue
            for nm in re.finditer(r"'([^']+)'", items):
                add(f"%{{_datadir}}/bash-completion/completions/{nm.group(1)}")
        for m in re.finditer(
            r"install_data\s*\(\s*'([^']+)'\s*,\s*install_dir:\s*[^\n]*bash-completion[^\n]*",
            text,
        ):
            block = m.group(0)
            # Multi-line install_data: pull a short window after the match
            start = m.start()
            window = text[start : start + 400]
            ren = re.search(r"rename:\s*'([^']+)'", window)
            if ren:
                add(f"%{{_datadir}}/bash-completion/completions/{ren.group(1)}")
                continue
            # rename: varname handled by foreach above — skip basename fallback
            if re.search(r"rename\s*:\s*\w+", window):
                continue
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
    meson_name = meson_project_name(root, name)

    # Python purelib (pypkgdir = …/dist-packages/…/project_name)
    if re.search(r"pypkgdir\s*=\s*[^\n]*dist-packages", text) and re.search(
        r"install_dir:\s*pypkgdir\b", text
    ):
        add(f"%{{_prefix}}/lib/python3/dist-packages/{meson_name}/*")

    # pkgdatadir = datadir / project_name() — install path follows Meson
    # project name (may differ from RPM Name; zfr RPM → share/zephyr/).
    if re.search(
        r"pkgdatadir\s*=\s*datadir\s*/\s*(?:meson\.project_name\(\)|"
        rf"['\"]{re.escape(meson_name)}['\"]|"
        rf"['\"]{re.escape(name)}['\"])",
        text,
    ) and re.search(r"install_dir:\s*pkgdatadir\b", text):
        add(f"%{{_datadir}}/{meson_name}/")

    # Extra pkgdata / perl modules / shared data / headers
    if re.search(
        rf"install_dir:\s*[^\n]*datadir[^\n]*/\s*(?:meson\.project_name\(\)|"
        rf"'{re.escape(meson_name)}'|'{re.escape(name)}')\s*[,)]",
        text,
    ):
        # Avoid counting setup-only installs as pkgdata.
        pkg_installs = [
            m.group(0)
            for m in re.finditer(r"install_dir:\s*[^\n]+", text)
            if "datadir" in m.group(0)
            and (
                "project_name" in m.group(0)
                or f"'{meson_name}'" in m.group(0)
                or f"'{name}'" in m.group(0)
            )
            and "setup" not in m.group(0)
            and "doc" not in m.group(0)
            and "bash-completion" not in m.group(0)
            and "bash-alias" not in m.group(0)
        ]
        if pkg_installs:
            add(f"%{{_datadir}}/{meson_name}/")
    # Templates copied via install script to datadir / project_name
    if re.search(
        r"(?:get_option\(\s*['\"]datadir['\"]\s*\)|datadir)\s*/\s*"
        r"(?:meson\.project_name\(\)|"
        rf"['\"]{re.escape(meson_name)}['\"]|"
        rf"['\"]{re.escape(name)}['\"])",
        text,
    ) and re.search(r"add_install_script|install_templates", text):
        add(f"%{{_datadir}}/{meson_name}/")
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

    # Only list setup/ when Meson actually installs there — postinst.in alone
    # is not enough (empty Makefile.am projects may keep the .in files unused).
    if re.search(
        r"['\"]setup['\"]\s*/\s*meson\.project_name"
        r"|datadir\s*/\s*['\"]setup['\"]",
        text,
    ):
        add("%{_datadir}/setup/%{name}/")


    mo = gettext_mo_line(root, name)
    if mo:
        add(mo)
    for line in locale_man_lines(root, name):
        add(line)

    add(f"%{{_datadir}}/doc/{meson_name}/")
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
