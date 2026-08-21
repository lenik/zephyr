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

from . import (
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
from .commands import (
    DEFAULT_AUTHOR,
    DEFAULT_DISTRIBUTION,
    DEFAULT_EMAIL,
    DEFAULT_INIT_VERSION,
    _install_githooks,
    _meson_project_fields,
    _write_debian_changelog,
)
from .csr import Csr
from .lint import _control, _role, _specs

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


def render_spec(root: Path, lang: str, name: str) -> str:
    src, pkg, _ = _control(root)
    desc = pkg.get("Description") or src.get("Description") or name
    summary = desc.split("\n", 1)[0].strip()
    long = desc.split("\n", 1)[1].strip() if "\n" in desc else summary
    long = "\n".join(ln.strip() for ln in long.split("\n"))
    homepage = _homepage(root)
    author, email = _maintainer(root)
    arch = (pkg.get("Architecture") or "any").strip()
    br = _split_deps(src.get("Build-Depends", ""))
    if "meson" not in br:
        br = ["meson", "ninja-build", *br]
    if "asciidoctor" not in br:
        br.append("asciidoctor")
    req = _split_deps(pkg.get("Depends", ""))
    buildarch = "BuildArch:      noarch\n" if arch == "all" else ""
    br_block = "\n".join(f"BuildRequires:  {n}" for n in br)
    req_block = "\n".join(f"Requires:       {n}" for n in req)
    if req_block:
        req_block = req_block + "\n"
    files = "\n".join(_spec_files(root, lang, name))
    return (
        "# Version is injected by rpm/Makefile via `zfr version`.\n"
        "# RPM Version cannot contain '-'; use `zfr version -r` "
        "(hyphens → '_').\n"
        "# srcversion is the unsanitized Meson/git version and names the tarball.\n"
        "%{!?version:%global version 0.0.0}\n"
        "%{!?srcversion:%global srcversion %{version}}\n"
        "\n"
        f"Name:           {name}\n"
        "Version:        %{version}\n"
        "Release:        1%{?dist}\n"
        f"Summary:        {summary}\n"
        "\n"
        f"License:        {_AGPL}\n"
        f"URL:            {homepage}\n"
        f"Packager:       {author} <{email}>\n"
        "Source0:        %{name}-%{srcversion}.tar.xz\n"
        "\n"
        f"{buildarch}{br_block}\n"
        f"{req_block}"
        f"\n%description\n{long}\n"
        "\n%prep\n"
        "%setup -q -n %{name}-%{srcversion}\n"
        "\n%build\n"
        "meson setup build \\\n"
        "    --prefix=%{_prefix} \\\n"
        "    --bindir=%{_bindir} \\\n"
        "    --datadir=%{_datadir} \\\n"
        "    --mandir=%{_mandir} \\\n"
        "    --sysconfdir=%{_sysconfdir} \\\n"
        "    --localstatedir=%{_localstatedir} \\\n"
        "    --buildtype=plain\n"
        "meson compile -C build\n"
        "\n%install\n"
        "meson install -C build --destdir=%{buildroot}\n"
        f"\n%files\n{files}\n"
        "\n%changelog\n"
        f"* Thu Aug 20 2026 {author} <{email}>\n"
        "- Align spec with debian/control (Meson, AGPL-3.0-or-later).\n"
        "- Version comes from `zfr version`, the same method meson.build uses.\n"
    )


def _man_target(name: str) -> str:
    return f"""
custom_target(
    '{name}-man',
    input: 'docs/{name}.adoc',
    output: '{name}.1',
    command: [
        asciidoctor,
        '-b', 'manpage',
        '-a', 'project-version=' + meson.project_version(),
        '-a', 'project-year=@0@'.format(project_year),
        '-a', 'project-author=' + project_author,
        '-a', 'project-email=' + project_email,
        '-o', '@OUTPUT@',
        '@INPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: mandir / 'man1',
)
"""


def groff_to_adoc(text: str, name: str, section: str = "1") -> str:
    """Best-effort groff man → AsciiDoc (used when pandoc is unavailable)."""
    body: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith('.\\"') or line.startswith("'\\\""):
            continue
        if line.startswith(".TH"):
            continue
        m = re.match(r"^\.SH\s+(.*)$", line, re.I)
        if m:
            title = m.group(1).strip().strip('"')
            body.append("")
            body.append(f"== {title.title() if title.isupper() else title}")
            body.append("")
            continue
        if line.startswith(".SS"):
            title = line[3:].strip().strip('"')
            body.append("")
            body.append(f"=== {title}")
            body.append("")
            continue
        if line in (".PP", ".P", ".LP", ".br"):
            body.append("")
            continue
        if line.startswith(".TP"):
            body.append("")
            continue
        line = re.sub(r"\\fB(.*?)\\f[PR]", r"*\1*", line)
        line = re.sub(r"\\fI(.*?)\\f[PR]", r"_\1_", line)
        line = line.replace("\\-", "-").replace("\\&", "")
        if line.startswith("."):
            continue
        body.append(line)
    inner = "\n".join(body).strip() or f"{name} command."
    return (
        f"= {name}({section})\n"
        "{project-author} <{project-email}>\n"
        "v{project-version}, {project-year}\n"
        ":doctype: manpage\n"
        ":manmanual: User Commands\n"
        f":mansource: {name}\n"
        ":man-linkstyle: blue R <>\n"
        ":nofooter:\n"
        "\n"
        f"{inner}\n"
        "\n"
        "== Author\n"
        "\n"
        "Written by {project-author} <{project-email}>.\n"
        "\n"
        "== Copyright\n"
        "\n"
        "Copyright (C) {project-year}.\n"
        f"License {_AGPL}.\n"
    )


def convert_man_file(path: Path, name: str) -> str:
    if shutil.which("pandoc"):
        proc = subprocess.run(
            ["pandoc", "-f", "man", "-t", "asciidoc", "--wrap=none", str(path)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            body = proc.stdout.strip()
            if not body.lstrip().startswith("= "):
                body = f"= {name}(1)\n\n{body}"
            header = (
                "{project-author} <{project-email}>\n"
                "v{project-version}, {project-year}\n"
                ":doctype: manpage\n"
                ":manmanual: User Commands\n"
                f":mansource: {name}\n"
                ":man-linkstyle: blue R <>\n"
                ":nofooter:\n"
            )
            if ":doctype: manpage" not in body:
                parts = body.split("\n", 1)
                body = parts[0] + "\n" + header + (parts[1] if len(parts) > 1 else "")
            return body if body.endswith("\n") else body + "\n"
    return groff_to_adoc(path.read_text(encoding="utf-8", errors="ignore"), name)


class Ize:
    def __init__(
        self,
        root: Path,
        *,
        lang: str,
        dry_run: bool = False,
        do_man: bool = True,
        do_subst: bool = True,
        verbose: bool = False,
        color: str = "auto",
    ) -> None:
        self.root = root
        self.lang = lang
        self.dry_run = dry_run
        self.do_man = do_man
        self.do_subst = do_subst
        self.verbose = verbose
        self.csr = Csr(color)
        self.changes: list[Change] = []
        meson = _meson_project_fields(root)
        src, _, _ = _control(root)
        self.name = src.get("Source") or meson.get("name") or root.name
        self.pairs = instantiation_pairs(self.name)

    def note(self, kind: str, path: str, detail: str) -> None:
        self.changes.append(Change(kind, path, detail))

    def write_text(self, path: Path, text: str, detail: str, *, kind: str = "add") -> None:
        rel = _rel(self.root, path)
        existed = path.is_file()
        if existed:
            kind = "update"
        self.note(kind, rel, detail)
        if self.dry_run:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def copy_file(self, src: Path, dest: Path, detail: str) -> None:
        rel = _rel(self.root, dest)
        self.note("add", rel, detail)
        if self.dry_run:
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        copy_renamed_file(src, dest, self.pairs)
        if dest.name in {"rules", "pre-commit"}:
            mode = dest.stat().st_mode
            dest.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def run(self) -> int:
        self.add_missing_files()
        self.ensure_changelog_version()
        self.ensure_hooks()
        self.patch_meson()
        if self.do_man:
            self.convert_manpages()
            self.patch_meson_man_targets()
        self.ensure_rpm()
        if self.do_subst:
            self.subst_versions()
        self.report()
        return 0

    def add_missing_files(self) -> None:
        try:
            tmpl = template_dir(self.lang)
        except SystemExit:
            tmpl = None
        if tmpl is not None and tmpl.resolve() == self.root.resolve():
            tmpl_copy = tmpl
        else:
            tmpl_copy = tmpl
        meson_dest = self.root / "meson.build"
        if not meson_dest.is_file() and tmpl_copy is not None:
            src = tmpl_copy / "meson.build"
            if src.is_file():
                self.copy_file(src, meson_dest, "meson.build from language template")
        if tmpl_copy is None:
            return
        for rel in SCAFFOLD:
            dest = self.root / rel
            src = tmpl_copy / rel
            if dest.exists():
                if self.verbose:
                    self.note("skip", rel, "already present")
                continue
            if not src.is_file():
                continue
            self.copy_file(src, dest, f"from {self.lang} template")

    def ensure_changelog_version(self) -> None:
        changelog = self.root / "debian" / "changelog"
        if not changelog.is_file():
            if self.dry_run:
                self.note("add", "debian/changelog", "initial changelog")
            else:
                author, email = _maintainer(self.root)
                ver = version_file_version(self.root) or DEFAULT_INIT_VERSION
                _write_debian_changelog(
                    self.root,
                    package=self.name,
                    version=ver,
                    distribution=DEFAULT_DISTRIBUTION,
                    author=author,
                    email=email,
                )
                self.note("add", "debian/changelog", f"{self.name} ({ver})")
        ver = changelog_version(self.root)
        version_path = self.root / "VERSION"
        if ver and (not version_path.is_file() or version_file_version(self.root) != ver):
            self.write_text(version_path, ver + "\n", "snapshot of debian/changelog")

    def ensure_hooks(self) -> None:
        hook = self.root / ".githooks" / "pre-commit"
        if hook.is_file():
            if self.verbose:
                self.note("skip", ".githooks/pre-commit", "already present")
            return
        if self.dry_run:
            self.note("add", ".githooks/pre-commit", "VERSION sync hook")
            return
        _install_githooks(self.root)
        if hook.is_file():
            self.note("add", ".githooks/pre-commit", "VERSION sync hook")
            git = shutil.which("git")
            if git and (self.root / ".git").exists():
                subprocess.run(
                    [git, "config", "core.hooksPath", ".githooks"],
                    cwd=self.root,
                    check=False,
                )

    def patch_meson(self) -> None:
        path = self.root / "meson.build"
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
            if re.search(r"version:\s*'[^']+'", proj or text):
                text = re.sub(
                    r"version:\s*'[^']+'",
                    lambda _m: "version: " + VERSION_RUN,
                    text,
                    count=1,
                )
                details.append("replace hardcoded project version")
            elif proj_end and "version:" not in proj:
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
            extra = ""
            if "license:" not in text[: end + 80] and _AGPL not in text[:end]:
                # license may be inside project()
                if "license:" not in text[text.find("project(") : end]:
                    extra_license = f",\n    license: '{_AGPL}'"
                    # insert before closing paren
                    text = text[: end - 1] + extra_license + text[end - 1 :]
                    insert_at = end + len(extra_license)
                    details.append("license AGPL-3.0-or-later")
                    end = insert_at
            after = text[end:]
            author, email = _maintainer(self.root)
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
                list((self.root / "docs").glob("*.adoc"))
                if (self.root / "docs").is_dir()
                else []
            )
        ]
        for adoc in docs:
            needle = f"docs/{adoc.name}"
            if needle not in text and f"'{adoc.name}'" not in text:
                text += _man_target(adoc.stem)
                details.append(f"man target {adoc.stem}")

        if not re.search(r"run_target\s*\(\s*['\"]look['\"]", text):
            text += LOOK_TARGET
            details.append("run_target look")

        license_files = [
            n for n in ("LICENSE", "README.md", "README-zh.md") if (self.root / n).is_file()
        ]
        if license_files and "install_dir: pkgdocdir" not in text:
            quoted = ",\n        ".join(f"'{n}'" for n in license_files)
            text += (
                "\ninstall_data(\n    [\n        "
                + quoted
                + ",\n    ],\n    install_dir: pkgdocdir,\n)\n"
            )
            details.append("install LICENSE/README")

        completions = list(self.root.glob("*.bash"))
        if completions and "bash-completion" not in text:
            names = ",\n    ".join(f"'{p.name}'" for p in completions)
            text += f"""
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
            details.append("install bash-completion")

        if text != orig:
            self.write_text(path, text if text.endswith("\n") else text + "\n", ", ".join(details))

    def convert_manpages(self) -> None:
        docs = self.root / "docs"
        for path in list(iter_files(self.root)):
            if path.suffix != ".1" and not path.name.endswith(".1.in"):
                continue
            if any(part in SKIP_MAN_PARTS for part in path.resolve().relative_to(self.root.resolve()).parts):
                continue
            stem = path.name[:-5] if path.name.endswith(".1.in") else path.stem
            dest = docs / f"{stem}.adoc"
            if dest.is_file():
                if self.verbose:
                    self.note("skip", _rel(self.root, dest), "adoc already exists")
                continue
            try:
                adoc = convert_man_file(path, stem)
            except OSError as e:
                self.note("skip", _rel(self.root, path), f"convert failed: {e}")
                continue
            if len(adoc.strip()) < 40:
                self.note("skip", _rel(self.root, path), "conversion too small")
                continue
            self.write_text(dest, adoc, f"from {_rel(self.root, path)}", kind="convert")
            rel_src = _rel(self.root, path)
            if path.parent in (self.root, self.root / "docs", self.root / "man"):
                self.note("convert", rel_src, "removed groff source; meson generates .1")
                if not self.dry_run:
                    path.unlink(missing_ok=True)
            meson = self.root / "meson.build"
            if meson.is_file():
                text = meson.read_text(encoding="utf-8")
                new = text
                new = re.sub(
                    rf"[ \t]*install_man\s*\(\s*['\"]{re.escape(rel_src)}['\"]\s*\)[ \t]*\n?",
                    "",
                    new,
                )
                new = re.sub(
                    rf"['\"]{re.escape(rel_src)}['\"]",
                    f"'docs/{stem}.adoc'",
                    new,
                )
                if new != text:
                    self.write_text(meson, new, f"stop installing source {rel_src}")

    def patch_meson_man_targets(self) -> None:
        path = self.root / "meson.build"
        if not path.is_file() or not (self.root / "docs").is_dir():
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
        for adoc in sorted((self.root / "docs").glob("*.adoc")):
            if f"docs/{adoc.name}" in text or f"{adoc.stem}-man" in text:
                continue
            text += _man_target(adoc.stem)
            details.append(f"man target {adoc.stem}")
        if text != orig:
            self.write_text(path, text if text.endswith("\n") else text + "\n", ", ".join(details))

    def ensure_rpm(self) -> None:
        makefile_dest = self.root / "rpm" / "Makefile"
        if not makefile_dest.is_file():
            src = None
            try:
                cand = template_dir(self.lang) / "rpm" / "Makefile"
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
                cand = here.parents[2] / "bash" / "rpm" / "Makefile"
                if cand.is_file():
                    src = cand
            if src is not None:
                self.copy_file(src, makefile_dest, "rpm/Makefile")
        specs = _specs(self.root)
        spec_path = self.root / "rpm" / f"{self.name}.spec"
        legacy = self.root / "rpm" / "zephyr.spec"
        if not specs:
            dest = spec_path if self.name != "zephyr" else legacy
            self.write_text(
                dest,
                render_spec(self.root, self.lang, self.name),
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
            if new != text:
                self.write_text(specs[0], new, ", ".join(details) or "spec touch-up")

    def subst_versions(self) -> None:
        ver = changelog_version(self.root) or version_file_version(self.root)
        if not ver or ver in {"0.0.0"}:
            return
        tokens = {ver, ver.lstrip("v")}
        if ver.startswith("v"):
            tokens.add(ver[1:])
        src_root = self.root / "src"
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
                if self.lang in _C_FAMILY and path.suffix in {".c", ".h", ".cpp", ".hpp", ".cc"}:
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
            if self.lang in _C_FAMILY and path.suffix in {".c", ".h", ".cpp", ".hpp", ".cc"}:
                self.write_text(path, new, f"use PROJECT_VERSION instead of {ver}")
                self._ensure_config_h()
                continue
            # scripts → .in
            dest = path.with_name(path.name + ".in")
            if dest.exists():
                continue
            rel_in = _rel(self.root, dest)
            self.write_text(dest, new, f"@VERSION@ subst from {_rel(self.root, path)}")
            converted.append(dest)
            if not self.dry_run:
                path.unlink()
            self.note("convert", _rel(self.root, path), f"replaced by {rel_in}")
        if converted:
            self._ensure_ize_scripts(converted)

    def _ensure_config_h(self) -> None:
        meson = self.root / "meson.build"
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
            self.write_text(
                meson,
                text.rstrip() + "\n" + snippet,
                "configure_file config.h with PROJECT_VERSION",
            )

    def _ensure_ize_scripts(self, ins: list[Path]) -> None:
        meson = self.root / "meson.build"
        if not meson.is_file():
            return
        rels = []
        for p in ins:
            rel = _rel(self.root, p).replace("\\", "/")
            rels.append(rel)
            if not self.dry_run:
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
        self.write_text(meson, text.rstrip() + "\n" + snippet, "configure_file for @VERSION@ scripts")

    def report(self) -> None:
        csr = self.csr
        adds = sum(1 for c in self.changes if c.kind == "add")
        updates = sum(1 for c in self.changes if c.kind == "update")
        converts = sum(1 for c in self.changes if c.kind == "convert")
        skips = sum(1 for c in self.changes if c.kind == "skip")
        head = csr.wrap("zfr ize", csr.bold)
        dry = "  dry-run" if self.dry_run else ""
        print(
            f"{head}: {self.root}  name={self.name}  lang={self.lang}{dry}",
            flush=True,
        )
        kind_color = {
            "add": csr.green,
            "update": csr.yellow,
            "convert": csr.cyan,
            "skip": csr.dim,
        }
        shown = [c for c in self.changes if c.kind != "skip" or self.verbose]
        for c in shown:
            tag = csr.wrap(f"{c.kind:7}", csr.bold, kind_color.get(c.kind, ""))
            path = csr.wrap(c.path, csr.bold, csr.blue)
            print(f"  {tag} {path}  {c.detail}", flush=True)
        print(
            f"done: {adds} added, {updates} updated, {converts} converted"
            + (f", {skips} skipped" if self.verbose else ""),
            flush=True,
        )
        if not self.dry_run:
            print("re-run `zfr lint` to check remaining style gaps.", flush=True)


def cmd_ize(
    *,
    lang: str | None = None,
    dry_run: bool = False,
    man: bool = True,
    subst: bool = True,
    verbose: bool = False,
    color: str = "auto",
    workdir: Path | None = None,
) -> int:
    root = find_project_dir(workdir)
    if _is_zfr_meta_repo(root):
        raise SystemExit(
            f"{root} looks like the zephyr meta-repo. "
            "Run zfr ize from a language project, not the repository root."
        )
    role = _role(root)
    if lang:
        if lang not in LANGS:
            raise SystemExit(f"unknown language {lang!r} (one of: {', '.join(LANGS)})")
        detected = lang
    else:
        try:
            detected = detect_lang(root)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            print("pass -l LANG to ize a project whose language could not be detected", file=sys.stderr)
            return 2
    if role == "meta":
        raise SystemExit("zfr ize does not operate on the meta-repo root")
    Ize(
        root,
        lang=detected,
        dry_run=dry_run,
        do_man=man,
        do_subst=subst,
        verbose=verbose,
        color=color,
    ).run()
    return 0
