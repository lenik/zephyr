# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize engine: bring a tree up to current zephyr style."""
from __future__ import annotations

from . import man as _man
from . import spec as _spec
from .debian import (
    ensure_debian_docs,
    ensure_debian_rules_meson,
    ensure_rpm_bash_shlib,
    ensure_rpm_noarch_nodebug,
    strip_rpm_substvars,
    patch_debian_control,
    strip_readme_banner,
)
from .rpm_files import _all_meson_texts, sync_rpm_files
from .util import *  # noqa: F403

convert_man_file = _man.convert_man_file
groff_to_adoc = _man.groff_to_adoc
_man_target = _man._man_target
strip_install_man_paths = _man.strip_install_man_paths
stub_man_adoc = _man.stub_man_adoc
discover_man_stems = _man.discover_man_stems
strip_help2man_blocks = _man.strip_help2man_blocks
render_spec = _spec.render_spec
# Names used by Ize methods copied from ize.py:
convert_man_file = convert_man_file
groff_to_adoc = groff_to_adoc
_man_target = _man_target
strip_install_man_paths = strip_install_man_paths
render_spec = render_spec

class Ize:
    def __init__(
        self,
        root: Path,
        *,
        lang: str,
        dry_run: bool = False,
        do_man: bool = True,
        do_subst: bool = True,
        do_mesonize: bool = True,
        do_commit: bool = False,
        verbose: bool = False,
        color: str = "auto",
    ) -> None:
        self.root = root
        self.lang = lang
        self.dry_run = dry_run
        self.do_man = do_man
        self.do_subst = do_subst
        self.do_mesonize = do_mesonize
        self.do_commit = do_commit
        self.verbose = verbose
        self.csr = Csr(color)
        self.changes: list[Change] = []
        self._mesonized = False
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
        self.mesonize()
        self.add_missing_files()
        self.patch_debian_control()
        self.ensure_debian_rules()
        self.fix_debian_docs()
        self.ensure_changelog_version()
        self.ensure_hooks()
        self.patch_meson()
        if self.do_man:
            self.convert_manpages()
            self.ensure_man_stubs()
            self.patch_meson_man_targets()
        # After man stubs, puff names are known — emit completions then refresh meson.
        self.ensure_completion()
        self.patch_meson()
        self.ensure_rpm()
        if self.do_subst:
            self.subst_versions()
        self.report()
        if self.do_commit:
            self.commit_changes()
        return 0

    def mesonize(self) -> None:
        """Convert Autotools/CMake to Meson via 2meson (default on)."""
        from .mesonize import find_2meson, has_foreign_build, run_2meson

        if not self.do_mesonize:
            if self.verbose:
                self.note("skip", "2meson", "--no-mesonize")
            return
        if not has_foreign_build(self.root):
            if self.verbose:
                self.note("skip", "2meson", "no Autotools/CMake sources")
            return
        exe = find_2meson()
        if exe is None:
            raise SystemExit(
                "zfr ize: Autotools/CMake detected but 2meson not found in PATH "
                "(install 2meson or set ZFR_2MESON)"
            )
        # Force overwrite when meson.build already exists alongside configure.ac
        # so a prior partial conversion can be refreshed.
        force = True
        detail = f"via {exe}"
        if self.dry_run:
            self.note("convert", "meson.build", f"would run 2meson {detail}")
            code, out = run_2meson(
                self.root, dry_run=True, force=force, verbose=self.verbose
            )
            if code != 0:
                raise SystemExit(f"zfr ize: 2meson dry-run failed (exit {code}):\n{out}")
            self._mesonized = True
            return
        code, out = run_2meson(
            self.root, dry_run=False, force=force, verbose=self.verbose
        )
        if code != 0:
            raise SystemExit(f"zfr ize: 2meson failed (exit {code}):\n{out}")
        self._mesonized = True
        self.note("convert", "meson.build", f"2meson {detail}")
        if self.verbose and out.strip():
            for line in out.strip().splitlines()[:20]:
                self.note("note", "2meson", line.strip())
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
        if (
            not meson_dest.is_file()
            and not self._mesonized
            and tmpl_copy is not None
        ):
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
            if rel in ("README.md", "README-zh.md"):
                raw = src.read_text(encoding="utf-8", errors="ignore")
                text = strip_readme_banner(raw, self.name)
                # Also swap template puff placeholders.
                text = text.replace(TEMPLATE_PUFF, self.name)
                text = text.replace("some_puff1", self.name)
                self.write_text(dest, text, f"from {self.lang} template (banner stripped)")
            else:
                self.copy_file(src, dest, f"from {self.lang} template")

    def patch_debian_control(self) -> None:
        path = self.root / "debian" / "control"
        if not path.is_file():
            return
        text = path.read_text(encoding="utf-8")
        new, notes = patch_debian_control(text, lang=self.lang)
        if new != text:
            self.write_text(path, new, ", ".join(notes) or "debian/control lint alignment")

    def ensure_debian_rules(self) -> None:
        path = self.root / "debian" / "rules"
        if not path.is_file():
            return
        text = path.read_text(encoding="utf-8", errors="ignore")
        new, notes = ensure_debian_rules_meson(text)
        if new != text:
            # Keep executable bit.
            mode = path.stat().st_mode
            self.write_text(path, new, ", ".join(notes) or "debian/rules")
            path.chmod(mode)

    def fix_debian_docs(self) -> None:
        notes = ensure_debian_docs(self.root)
        if notes:
            self.note("update", "debian/docs", ", ".join(notes))
    def ensure_man_stubs(self) -> None:
        """Create docs/*.adoc stubs when Autotools mans were help2man-only."""
        docs = self.root / "docs"
        existing = list(docs.glob("*.adoc")) if docs.is_dir() else []
        stems = discover_man_stems(self.root, self.name)
        # Only create stubs for stems that lack adoc.
        missing = [(s, sec) for s, sec in stems if not (docs / f"{s}.adoc").is_file()]
        if not missing and existing:
            # Still strip help2man if we already have adoc.
            meson = self.root / "meson.build"
            if meson.is_file():
                text = meson.read_text(encoding="utf-8")
                cleaned = strip_help2man_blocks(text)
                if cleaned != text:
                    self.write_text(meson, cleaned, "remove help2man blocks (AsciiDoc mans)")
            return
        if not missing:
            missing = [(self.name, "1")]
        summary = ""
        control = self.root / "debian" / "control"
        if control.is_file():
            m = re.search(
                r"^Description:\s*(.+)$",
                control.read_text(encoding="utf-8", errors="ignore"),
                re.M,
            )
            if m:
                summary = m.group(1).strip()
        for stem, section in missing:
            dest = docs / f"{stem}.adoc"
            body = stub_man_adoc(stem, section, summary=summary or f"{stem} utility")
            self.write_text(dest, body, "AsciiDoc man stub for lint/layout.docs")
        meson = self.root / "meson.build"
        if meson.is_file():
            text = meson.read_text(encoding="utf-8")
            cleaned = strip_help2man_blocks(text)
            if cleaned != text:
                self.write_text(meson, cleaned, "remove help2man blocks (AsciiDoc mans)")

    def ensure_completion(self) -> None:
        """Ensure a bash-completion stub exists for each command puff."""
        if self.lang != "bash":
            return
        puffs = _puff_names(self.root) or [self.name]
        for puff in puffs:
            dest = self.root / f"{puff}.bash"
            if dest.is_file():
                continue
            alt = self.root / "completions" / f"{puff}.bash"
            if alt.is_file():
                continue
            body = (
                f"# bash completion for {puff} (stub; extend as needed)\n"
                f"complete -F _longopt {puff} 2>/dev/null || true\n"
            )
            self.write_text(dest, body, f"bash-completion stub {puff}")

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

        completions = sorted(self.root.glob("*.bash"))
        if completions:
            names = ",\n    ".join(f"'{p.name}'" for p in completions)
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
                text += block
                details.append("install bash-completion")
            else:
                new_text, nsub = re.subn(
                    r"bash_files\s*=\s*\[[^\]]*\]",
                    "bash_files = [\n    " + names + ",\n]",
                    text,
                    count=1,
                    flags=re.S,
                )
                if nsub and new_text != text:
                    text = new_text
                    details.append("refresh bash-completion list")

        if text != orig:
            self.write_text(path, text if text.endswith("\n") else text + "\n", ", ".join(details))

    def convert_manpages(self) -> None:
        docs = self.root / "docs"
        man_re = re.compile(r"^(?P<stem>.+)\.(?P<section>[1-9][a-zA-Z]*)(?:\.in)?$")
        for path in list(iter_files(self.root)):
            m = man_re.match(path.name)
            if not m:
                continue
            rel_parts = path.resolve().relative_to(self.root.resolve()).parts
            if any(part in SKIP_MAN_PARTS for part in rel_parts):
                continue
            stem = m.group("stem")
            section = m.group("section")
            dest = docs / f"{stem}.adoc"
            if dest.is_file():
                if self.verbose:
                    self.note("skip", _rel(self.root, dest), "adoc already exists")
                continue
            try:
                adoc = convert_man_file(path, stem, section=section)
            except OSError as e:
                self.note("skip", _rel(self.root, path), f"convert failed: {e}")
                continue
            if len(adoc.strip()) < 40:
                self.note("skip", _rel(self.root, path), "conversion too small")
                continue
            self.write_text(dest, adoc, f"from {_rel(self.root, path)}", kind="convert")
            rel_src = _rel(self.root, path)
            if path.parent in (self.root, self.root / "docs", self.root / "man"):
                self.note("convert", rel_src, "removed groff source; meson generates manpage")
                if not self.dry_run:
                    path.unlink(missing_ok=True)
            meson = self.root / "meson.build"
            if meson.is_file():
                text = meson.read_text(encoding="utf-8")
                new = strip_install_man_paths(
                    text, {rel_src, path.name, f"{stem}.{section}"}
                )
                if new != text:
                    self.write_text(meson, new, f"drop groff {rel_src} from install_man")

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
        # Strip leftover install_man(.../*.adoc) from a prior ize run.
        cleaned = strip_install_man_paths(text, set())
        if cleaned != text:
            text = cleaned
            details.append("remove AsciiDoc paths from install_man")
        for adoc in sorted((self.root / "docs").glob("*.adoc")):
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
                self.copy_file(src, makefile_dest, "rpm/Makefile")
        if makefile_dest.is_file():
            from ..packaging import migrate_rpm_makefile_topdir

            mk_text = makefile_dest.read_text(encoding="utf-8", errors="ignore")
            migrated = migrate_rpm_makefile_topdir(mk_text)
            if migrated is not None:
                self.write_text(
                    makefile_dest,
                    migrated if migrated.endswith("\n") else migrated + "\n",
                    "rpm/Makefile TOPDIR -> %_topdir ($HOME/rpmbuild)",
                )
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
            arch_bins = bool(
                re.search(r"\bexecutable\s*\(", _all_meson_texts(self.root))
            )
            if self.lang == "bash":
                patched, changed = ensure_rpm_bash_shlib(new)
                if changed:
                    new = patched
                    details.append("Requires bash-shlib")
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
            elif arch_bins:
                patched, changed = ensure_rpm_noarch_nodebug(
                    new, arch_binaries=True
                )
                if changed:
                    new = patched
                    details.append("drop noarch (ELF)")
            patched, changed = strip_rpm_substvars(new)
            if changed:
                new = patched
                details.append("strip Debian substvars from Requires")
            expected = _spec_files(self.root, self.lang, self.name)
            synced, file_notes = sync_rpm_files(new, expected=expected)
            if file_notes:
                new = synced
                details.extend(file_notes)
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
            "note": csr.dim,
        }
        shown = [c for c in self.changes if c.kind not in {"skip", "note"} or self.verbose]
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

    def commit_message(self) -> str:
        """Build a verbose commit message from recorded ize changes."""
        real = [c for c in self.changes if c.kind in {"add", "update", "convert"}]
        adds = sum(1 for c in real if c.kind == "add")
        updates = sum(1 for c in real if c.kind == "update")
        converts = sum(1 for c in real if c.kind == "convert")
        subject = f"zfr ize: align {self.name} (lang={self.lang}) to current zephyr style"
        lines = [
            subject,
            "",
            f"Automated `zfr ize` on {self.name}: bring packaging, Meson, man pages,",
            "and version substitutions up to current zephyr style.",
            "",
        ]
        if real:
            lines.append("Changes:")
            for c in real:
                lines.append(f"  - {c.kind:7} {c.path}: {c.detail}")
            lines.append("")
        lines.append(
            f"{adds} added, {updates} updated, {converts} converted"
            + ("; mesonized via 2meson" if self._mesonized else "")
            + "."
        )
        lines.append("")
        return "\n".join(lines)

    def commit_changes(self) -> None:
        """``git add -A`` and commit when there is something to record."""
        import subprocess

        def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["git", *args],
                cwd=self.root,
                check=check,
                capture_output=True,
                text=True,
            )

        try:
            git("rev-parse", "--is-inside-work-tree")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise SystemExit(
                f"zfr ize --commit: {self.root} is not a git working tree"
            ) from e

        real = [c for c in self.changes if c.kind in {"add", "update", "convert"}]
        if not real and not self._mesonized:
            print("zfr ize --commit: no ize changes to commit.", flush=True)
            return

        git("add", "-A")
        staged = git("diff", "--cached", "--quiet", check=False)
        if staged.returncode == 0:
            print("zfr ize --commit: working tree clean after ize; nothing to commit.", flush=True)
            return

        msg = self.commit_message()
        try:
            git("commit", "-m", msg)
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or "").strip() or str(e)
            raise SystemExit(f"zfr ize --commit failed: {err}") from e
        sha = git("rev-parse", "--short", "HEAD").stdout.strip()
        print(f"committed {sha}: {msg.splitlines()[0]}", flush=True)
