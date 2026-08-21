# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr lint — validate a project against zephyr packaging and layout style.

Output is meant for humans and AI coders: each finding has a code, location,
and a concrete fix. Interactive TTYs get CSR (console SGR) colors.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import (
    LANGS,
    TEMPLATE_PUFF,
    _is_zfr_meta_repo,
    changelog_version,
    detect_lang,
    find_project_dir,
    is_probably_text,
    iter_files,
    template_dir,
    version_file_version,
)
from .commands import _meson_project_fields, _parse_control_stanzas
from .csr import Csr

_PLACEHOLDER_README = "THIS FILE IS GENERATED FROM A TEMPLATE"
_PLACEHOLDER_README_ZH = "本文件由模板生成"
_AGPL = "AGPL-3.0-or-later"


@dataclass
class Finding:
    severity: str  # error, warn, note, ok
    code: str
    message: str
    file: str | None = None
    line: int | None = None
    fix: str | None = None


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _role(root: Path) -> str:
    if _is_zfr_meta_repo(root):
        return "meta"
    if _is_zfr_meta_repo(root.parent):
        return "template"
    return "app"


def _control(root: Path) -> tuple[dict[str, str], dict[str, str], str]:
    path = root / "debian" / "control"
    text = _read(path)
    stanzas = _parse_control_stanzas(text) if text else []
    src = stanzas[0] if stanzas else {}
    pkg = stanzas[1] if len(stanzas) > 1 else src
    return src, pkg, text


def _specs(root: Path) -> list[Path]:
    found: list[Path] = []
    rpm = root / "rpm"
    if rpm.is_dir():
        found.extend(sorted(rpm.glob("*.spec")))
    found.extend(sorted(root.glob("*.spec")))
    uniq: list[Path] = []
    seen: set[Path] = set()
    for p in found:
        r = p.resolve()
        if r in seen:
            continue
        seen.add(r)
        uniq.append(p)
    return uniq


def _has_file(root: Path, rel: str) -> bool:
    return (root / rel).is_file()


def _line_of(text: str, needle: str) -> int | None:
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return None


def check_layout(root: Path, lang: str, role: str) -> list[Finding]:
    out: list[Finding] = []
    required = [
        ("meson.build", "meson.build", "Add a top-level meson.build with project(...)."),
        ("LICENSE", "LICENSE", "Copy LICENSE from the language template (AGPL-3.0-or-later)."),
        ("README.md", "README.md", "Add README.md describing this project."),
        ("README-zh.md", "README-zh.md", "Add README-zh.md (Chinese summary), matching other zephyr templates."),
        ("debian/control", "debian/control", "Add debian/ packaging (copy debian/ from the language template)."),
        ("debian/changelog", "debian/changelog", "Add debian/changelog (zfr create writes one; or use dch)."),
        ("debian/copyright", "debian/copyright", "Add debian/copyright in machine-readable format, License: AGPL-3+."),
        ("debian/rules", "debian/rules", "Add debian/rules using dh --buildsystem=meson --builddirectory=debian/build."),
        ("debian/source/format", "debian/source/format", "Add debian/source/format (typically '3.0 (native)')."),
    ]
    for code, rel, fix in required:
        if _has_file(root, rel):
            out.append(Finding("ok", f"layout.{code.replace('/', '.')}", f"present: {rel}", rel))
        else:
            out.append(
                Finding("error", f"layout.{code.replace('/', '.')}", f"missing {rel}", rel, fix=fix)
            )

    adocs = list((root / "docs").glob("*.adoc")) if (root / "docs").is_dir() else []
    if adocs:
        out.append(
            Finding("ok", "layout.docs", f"AsciiDoc man sources: {', '.join(p.name for p in adocs)}", "docs/")
        )
    else:
        out.append(
            Finding(
                "error",
                "layout.docs",
                "no docs/*.adoc man page source",
                "docs/",
                fix="Add docs/<puff>.adoc and a meson custom_target with asciidoctor -b manpage "
                "(see any language template).",
            )
        )

    completions = list(root.glob("*.bash"))
    if not completions and (root / "tools").is_dir():
        completions = list((root / "tools").glob("*.bash"))
    if completions:
        out.append(
            Finding(
                "ok",
                "layout.completion",
                f"bash completion: {', '.join(p.name for p in completions)}",
            )
        )
    elif role != "meta":
        out.append(
            Finding(
                "warn",
                "layout.completion",
                "no *.bash bash-completion script at project root",
                fix="Add <puff>.bash and install it to datadir/bash-completion/completions "
                "renamed to the command name (see meson.build in the template).",
            )
        )

    if _has_file(root, "VERSION"):
        out.append(Finding("ok", "layout.VERSION", "VERSION file present", "VERSION"))
    else:
        out.append(
            Finding(
                "warn",
                "layout.VERSION",
                "no VERSION file (changelog snapshot for tarball builds)",
                "VERSION",
                fix="Create VERSION with the latest debian/changelog version "
                "(one line). Enable .githooks/pre-commit: git config core.hooksPath .githooks",
            )
        )

    hook = root / ".githooks" / "pre-commit"
    if hook.is_file():
        out.append(Finding("ok", "layout.pre-commit", "pre-commit hook present", ".githooks/pre-commit"))
    else:
        out.append(
            Finding(
                "note",
                "layout.pre-commit",
                "no .githooks/pre-commit to sync VERSION from debian/changelog",
                ".githooks/pre-commit",
                fix="Copy .githooks/pre-commit from the zephyr tree; "
                "`zfr create` sets git config core.hooksPath .githooks.",
            )
        )
    return out


def check_identity(root: Path, lang: str, role: str) -> list[Finding]:
    out: list[Finding] = []
    meson = _meson_project_fields(root)
    src, pkg, _ = _control(root)
    dir_name = root.name
    meson_name = meson.get("name") or ""
    source = src.get("Source") or ""
    package = pkg.get("Package") or ""

    names = {
        "directory": dir_name,
        "meson.project": meson_name,
        "debian.Source": source,
        "debian.Package": package,
    }
    if role == "app":
        expected = dir_name
        for label, val in names.items():
            if not val:
                continue
            if val != expected:
                out.append(
                    Finding(
                        "error",
                        f"identity.{label}",
                        f"{label} is {val!r}, expected {expected!r} (directory name)",
                        "meson.build" if label.startswith("meson") else "debian/control",
                        fix=f"Set {label} to {expected!r}, or rename the directory. "
                        "Use `zfr rename {expected}` if leftover template names remain.",
                    )
                )
            else:
                out.append(Finding("ok", f"identity.{label}", f"{label}={val}"))
    else:
        if meson_name:
            out.append(Finding("ok", "identity.meson.project", f"meson project name={meson_name}"))
        if source and meson_name and source != meson_name:
            out.append(
                Finding(
                    "warn",
                    "identity.source_vs_meson",
                    f"debian Source={source!r} != meson project={meson_name!r}",
                    "debian/control",
                    fix="Keep Source, Package, and meson project() name identical.",
                )
            )
        elif source:
            out.append(Finding("ok", "identity.debian.Source", f"Source={source}"))

    specs = _specs(root)
    if specs:
        text = _read(specs[0])
        m = re.search(r"^Name:\s*(\S+)", text, re.M)
        spec_name = m.group(1) if m else ""
        want = source or meson_name or dir_name
        if spec_name and want and spec_name != want:
            out.append(
                Finding(
                    "error",
                    "identity.rpm.Name",
                    f"spec Name={spec_name!r} != debian/meson name {want!r}",
                    _rel(root, specs[0]),
                    line=_line_of(text, "Name:"),
                    fix=f"Set Name: {want} in the spec (same as debian Source).",
                )
            )
        elif spec_name:
            out.append(Finding("ok", "identity.rpm.Name", f"spec Name={spec_name}", _rel(root, specs[0])))
    return out


def check_meson(root: Path, lang: str) -> list[Finding]:
    out: list[Finding] = []
    path = root / "meson.build"
    if not path.is_file():
        return out
    text = _read(path)
    rel = "meson.build"

    if re.search(r"^\s*project\s*\(", text, re.M):
        out.append(Finding("ok", "meson.project", "project() present", rel))
    else:
        out.append(
            Finding(
                "error",
                "meson.project",
                "meson.build has no project() call",
                rel,
                fix="project() must be the first Meson call. Copy the header from the language template.",
            )
        )

    if _AGPL in text:
        out.append(Finding("ok", "meson.license", f"license {_AGPL}", rel))
    else:
        out.append(
            Finding(
                "warn",
                "meson.license",
                "meson license is not AGPL-3.0-or-later",
                rel,
                line=_line_of(text, "license"),
                fix=f"Set license: '{_AGPL}' in project().",
            )
        )

    for var in ("project_author", "project_email", "project_year"):
        if var in text:
            out.append(Finding("ok", f"meson.{var}", f"{var} set", rel))
        else:
            out.append(
                Finding(
                    "warn",
                    f"meson.{var}",
                    f"missing {var} (used for man pages)",
                    rel,
                    fix=f"Set {var} next to project(), then pass -a project-author/email/year to asciidoctor.",
                )
            )

    if "zfr version" in text:
        out.append(Finding("ok", "meson.version_source", "version uses `zfr version`", rel))
    elif "git describe" in text:
        out.append(
            Finding(
                "warn",
                "meson.version_source",
                "version still uses inline git describe; zephyr style is `zfr version`",
                rel,
                line=_line_of(text, "git describe"),
                fix="In project(version: run_command(...)), prefer:\n"
                "  v=$(zfr version 2>/dev/null || true)\n"
                "  with fallback v=\"0.0.0\" # FIXED TO 0.0.0, DO NOT MODIFY\n"
                "See bash/meson.build in the zephyr tree.",
            )
        )
    else:
        out.append(
            Finding(
                "warn",
                "meson.version_source",
                "could not find `zfr version` or git describe in project version",
                rel,
                fix="Use `zfr version` for project() version (see bash/meson.build).",
            )
        )

    if 'FIXED TO 0.0.0' in text or 'v="0.0.0"' in text:
        out.append(Finding("ok", "meson.version_fallback", "0.0.0 fallback present", rel))
    else:
        out.append(
            Finding(
                "note",
                "meson.version_fallback",
                "no explicit 0.0.0 fallback for missing git/VERSION",
                rel,
                fix='Keep fallback v="0.0.0" # FIXED TO 0.0.0, DO NOT MODIFY',
            )
        )

    if "asciidoctor" in text:
        out.append(Finding("ok", "meson.asciidoctor", "asciidoctor man pages", rel))
    else:
        out.append(
            Finding(
                "error",
                "meson.asciidoctor",
                "meson.build does not invoke asciidoctor",
                rel,
                fix="find_program('asciidoctor') and custom_target(..., '-b', 'manpage', ...).",
            )
        )

    if re.search(r"run_target\s*\(\s*['\"]look['\"]", text):
        out.append(Finding("ok", "meson.look", "run_target look present", rel))
    else:
        out.append(
            Finding(
                "note",
                "meson.look",
                "no run_target('look') DESTDIR preview",
                rel,
                fix="Add run_target look that meson install's into a tempdir and runs tree (see templates).",
            )
        )

    if "bash-completion" in text:
        out.append(Finding("ok", "meson.completion_install", "installs bash-completion", rel))
    else:
        out.append(
            Finding(
                "warn",
                "meson.completion_install",
                "does not install bash-completion",
                rel,
                fix="install_data(..., install_dir: datadir / 'bash-completion' / 'completions', rename: command).",
            )
        )
    return out


def check_debian(root: Path, lang: str, role: str) -> list[Finding]:
    out: list[Finding] = []
    src, pkg, text = _control(root)
    rel = "debian/control"
    if not text:
        return out

    bd = src.get("Build-Depends", "")
    for dep in ("meson", "ninja-build", "asciidoctor"):
        if re.search(rf"\b{re.escape(dep)}\b", bd):
            out.append(Finding("ok", f"debian.build-depends.{dep}", f"Build-Depends has {dep}", rel))
        else:
            out.append(
                Finding(
                    "error",
                    f"debian.build-depends.{dep}",
                    f"Build-Depends missing {dep}",
                    rel,
                    fix=f"Add {dep} to Build-Depends (zephyr packages build with Meson + AsciiDoc man pages).",
                )
            )
    if "debhelper-compat" in bd:
        out.append(Finding("ok", "debian.debhelper", "debhelper-compat present", rel))
    else:
        out.append(
            Finding(
                "warn",
                "debian.debhelper",
                "Build-Depends missing debhelper-compat (= 13)",
                rel,
                fix="Build-Depends: debhelper-compat (= 13), meson, ninja-build, asciidoctor",
            )
        )

    arch = pkg.get("Architecture", "")
    if not arch:
        out.append(
            Finding(
                "error",
                "debian.Architecture",
                "Package stanza missing Architecture",
                rel,
                fix="Architecture: all  (scripts) or any (compiled).",
            )
        )
    elif lang == "bash" and arch != "all":
        out.append(
            Finding(
                "warn",
                "debian.Architecture",
                f"bash packages should be Architecture: all (got {arch})",
                rel,
                fix="Architecture: all",
            )
        )
    elif lang in ("c", "clib", "cpp", "cpplib", "rust", "go", "haskell") and arch == "all":
        out.append(
            Finding(
                "warn",
                "debian.Architecture",
                f"{lang} packages are usually Architecture: any (got all)",
                rel,
                fix="Architecture: any",
            )
        )
    else:
        out.append(Finding("ok", "debian.Architecture", f"Architecture: {arch}", rel))

    homepage = src.get("Homepage", "")
    if homepage:
        out.append(Finding("ok", "debian.Homepage", f"Homepage: {homepage}", rel))
    else:
        out.append(
            Finding(
                "warn",
                "debian.Homepage",
                "no Homepage",
                rel,
                fix="Set Homepage: to the project URL.",
            )
        )

    rules = _read(root / "debian" / "rules")
    if "buildsystem=meson" in rules and "debian/build" in rules:
        out.append(Finding("ok", "debian.rules", "dh meson debian/build", "debian/rules"))
    elif rules:
        out.append(
            Finding(
                "warn",
                "debian.rules",
                "debian/rules is not dh --buildsystem=meson --builddirectory=debian/build",
                "debian/rules",
                fix="Use:\n#!/usr/bin/make -f\n\n%:\n\tdh $@ --buildsystem=meson --builddirectory=debian/build",
            )
        )

    copyr = _read(root / "debian" / "copyright")
    if "AGPL" in copyr:
        out.append(Finding("ok", "debian.copyright", "copyright mentions AGPL", "debian/copyright"))
    elif copyr:
        out.append(
            Finding(
                "warn",
                "debian.copyright",
                "debian/copyright does not mention AGPL",
                "debian/copyright",
                fix="Use the template debian/copyright (License: AGPL-3+).",
            )
        )

    fmt = _read(root / "debian" / "source" / "format").strip()
    if fmt:
        out.append(Finding("ok", "debian.source.format", f"source format {fmt}", "debian/source/format"))

    ch_ver = changelog_version(root)
    file_ver = version_file_version(root)
    if ch_ver and file_ver and ch_ver.lstrip("v") != file_ver.lstrip("v"):
        out.append(
            Finding(
                "warn",
                "debian.VERSION_sync",
                f"VERSION={file_ver!r} != changelog {ch_ver!r}",
                "VERSION",
                fix="VERSION should match the latest debian/changelog entry "
                "(pre-commit hook updates it). Git describe may still differ.",
            )
        )
    elif ch_ver and file_ver:
        out.append(
            Finding("ok", "debian.VERSION_sync", f"VERSION matches changelog {ch_ver}", "VERSION")
        )

    if lang == "bash":
        deps = pkg.get("Depends", "")
        if "bash-shlib" not in deps:
            out.append(
                Finding(
                    "error",
                    "debian.Depends.bash-shlib",
                    "bash project Depends missing bash-shlib",
                    rel,
                    fix="Depends: bash, bash-shlib, ${misc:Depends}",
                )
            )
        else:
            out.append(Finding("ok", "debian.Depends.bash-shlib", "Depends includes bash-shlib", rel))
    return out


def check_rpm(root: Path, lang: str) -> list[Finding]:
    out: list[Finding] = []
    specs = _specs(root)
    src, pkg, _ = _control(root)
    if not specs:
        out.append(
            Finding(
                "note",
                "rpm.missing",
                "no rpm/*.spec (optional, but zephyr style includes RPM next to debian/)",
                "rpm/",
                fix="Copy rpm/ (zephyr.spec + Makefile using `zfr version`) from the "
                "zephyr tree and rewrite names. Align Name/Summary/Requires/URL with debian/control.",
            )
        )
        return out

    spec = specs[0]
    rel = _rel(root, spec)
    text = _read(spec)
    makefile = root / "rpm" / "Makefile"
    mk = _read(makefile)

    if "%{version}" in text or "%{!?version" in text:
        out.append(Finding("ok", "rpm.dynamic_version", "spec Version is dynamic %{version}", rel))
    elif re.search(r"^Version:\s*[0-9]", text, re.M):
        out.append(
            Finding(
                "error",
                "rpm.dynamic_version",
                "spec Version is hardcoded; zephyr style injects `zfr version`",
                rel,
                line=_line_of(text, "Version:"),
                fix="Use Version: %{version} with %{!?version:%global version 0.0.0} "
                "and freeze via rpm/Makefile (`zfr version` / `zfr version -r`).",
            )
        )

    if _AGPL in text:
        out.append(Finding("ok", "rpm.license", f"License {_AGPL}", rel))
    else:
        out.append(
            Finding(
                "warn",
                "rpm.license",
                "spec License is not AGPL-3.0-or-later",
                rel,
                line=_line_of(text, "License:"),
                fix=f"License:        {_AGPL}",
            )
        )

    url = re.search(r"^URL:\s*(\S+)", text, re.M)
    homepage = src.get("Homepage", "")
    if url and homepage and url.group(1).rstrip("/") != homepage.rstrip("/"):
        out.append(
            Finding(
                "warn",
                "rpm.URL",
                f"spec URL={url.group(1)!r} != debian Homepage={homepage!r}",
                rel,
                fix="Set URL: to the same Homepage as debian/control.",
            )
        )

    summary = re.search(r"^Summary:\s*(.+)$", text, re.M)
    desc = pkg.get("Description", "")
    deb_summary = desc.split("\n", 1)[0].strip() if desc else ""
    if summary and deb_summary and summary.group(1).strip() != deb_summary:
        out.append(
            Finding(
                "warn",
                "rpm.Summary",
                "spec Summary does not match debian Description first line",
                rel,
                line=_line_of(text, "Summary:"),
                fix=f"Summary:        {deb_summary}",
            )
        )

    if "meson" in text.lower() and "%configure" not in text:
        out.append(Finding("ok", "rpm.build", "spec uses Meson (not autotools)", rel))
    elif "%configure" in text or "autoreconf" in text:
        out.append(
            Finding(
                "error",
                "rpm.build",
                "spec still uses autotools; zephyr packages build with Meson",
                rel,
                fix="%build: meson setup build --prefix=%{_prefix} ... && meson compile -C build\n"
                "%install: meson install -C build --destdir=%{buildroot}",
            )
        )

    if makefile.is_file():
        if "zfr version" in mk:
            out.append(
                Finding("ok", "rpm.makefile.version", "Makefile uses `zfr version`", "rpm/Makefile")
            )
        else:
            out.append(
                Finding(
                    "warn",
                    "rpm.makefile.version",
                    "rpm/Makefile does not call `zfr version`",
                    "rpm/Makefile",
                    fix="VERSION := $(shell cd \"$(SRCDIR)\" && zfr version)\n"
                    "RPM_VERSION := $(shell cd \"$(SRCDIR)\" && zfr version -r)",
                )
            )
    else:
        out.append(
            Finding(
                "note",
                "rpm.makefile",
                "no rpm/Makefile convenience targets",
                "rpm/Makefile",
                fix="Copy bash/rpm/Makefile (srpm/rpm via zfr version).",
            )
        )

    if lang == "bash" and "bash-shlib" not in text:
        out.append(
            Finding(
                "error",
                "rpm.Requires.bash-shlib",
                "bash spec Requires missing bash-shlib",
                rel,
                fix="Requires:       bash-shlib  (same as debian Depends)",
            )
        )
    return out


def check_readme(root: Path, role: str) -> list[Finding]:
    out: list[Finding] = []
    for name in ("README.md", "README-zh.md"):
        path = root / name
        if not path.is_file():
            continue
        text = _read(path)
        marker = _PLACEHOLDER_README if name == "README.md" else _PLACEHOLDER_README_ZH
        has_banner = marker in text or _PLACEHOLDER_README in text
        if has_banner:
            if role == "template":
                out.append(
                    Finding(
                        "note",
                        f"readme.placeholder.{name}",
                        f"{name} keeps the template placeholder banner (apps must rewrite it)",
                        name,
                        line=1,
                        fix="After `zfr create`/`zfr rename`, rewrite this README and remove "
                        "the generated-from-template banner. Templates should keep this banner.",
                    )
                )
            else:
                out.append(
                    Finding(
                        "error",
                        f"readme.placeholder.{name}",
                        f"{name} still has the template placeholder banner",
                        name,
                        line=1,
                        fix=f"Rewrite {name} for this project. Remove the generated-from-template "
                        "banner and describe the real commands, build, and license.",
                    )
                )
        else:
            out.append(Finding("ok", f"readme.{name}", f"{name} has no template banner", name))
    return out


# Instantiated apps call the zfr CLI for version/dist. The tool name "zfr"
# is never a leftover template token. Legacy lines that still say
# "zephyr version" contain the placeholder word and are exempted here.
_ZEPHYR_CLI_LINE = re.compile(
    r"zephyr\s+version"
    r"|zephyr\s+dist"
    r"|zephyr\s+is expected"
    r"|zephyr\s+on PATH"
    r"|zephyr not found"
    r"|command\s+-v\s+zephyr"
    r"|tools/zephyr"
    r"|`zephyr\s+",
    re.I,
)


def _leftover_line(line: str, token: re.Pattern[str]) -> bool:
    if not token.search(line):
        return False
    return not _ZEPHYR_CLI_LINE.search(line)


def check_leftovers(root: Path, role: str) -> list[Finding]:
    if role != "app":
        return [
            Finding(
                "ok",
                "tokens.template",
                f"{role} tree may contain zephyr/some_puff1 placeholders (expected)",
            )
        ]
    hits = 0
    samples: list[str] = []
    token = re.compile(rf"\b({re.escape(TEMPLATE_PUFF)}|zephyr)\b", re.I)
    for path in iter_files(root):
        rel = path.relative_to(root)
        parts = {rel.as_posix(), path.name}
        if any(token.search(p) for p in parts) and "tools/zfr" not in rel.as_posix():
            hits += 1
            if len(samples) < 8:
                samples.append(str(rel))
        if not path.is_file() or not is_probably_text(path):
            continue
        text = _read(path)
        for i, line in enumerate(text.splitlines(), 1):
            if _leftover_line(line, token):
                hits += 1
                if len(samples) < 8:
                    samples.append(f"{rel}:{i}")
                break
    if hits:
        preview = ", ".join(samples)
        more = "" if hits <= 8 else f" (+{hits - len(samples)} more)"
        return [
            Finding(
                "error",
                "tokens.leftover",
                f"found {hits} leftover template token(s) (zephyr/{TEMPLATE_PUFF}): {preview}{more}",
                fix="Run `zfr rename <project> [puff ...]` or replace remaining zephyr/some_puff1 "
                "identifiers. After create, leftover tokens mean instantiation failed.",
            )
        ]
    return [Finding("ok", "tokens.leftover", "no leftover zephyr/some_puff1 tokens")]


def check_lang_bits(root: Path, lang: str) -> list[Finding]:
    out: list[Finding] = []
    if lang == "bash":
        ins = list((root / "src").glob("*.in")) if (root / "src").is_dir() else []
        if ins:
            out.append(Finding("ok", "lang.bash.src", f"src scripts: {', '.join(p.name for p in ins)}"))
        else:
            out.append(
                Finding(
                    "warn",
                    "lang.bash.src",
                    "no src/*.in scripts",
                    "src/",
                    fix="Keep configured scripts as src/<puff>.in with @PACKAGE@/@VERSION@ "
                    "and meson configure_file + install_mode rwxr-xr-x.",
                )
            )
    elif lang in ("c", "clib", "cpp", "cpplib"):
        if not (root / "tests").is_dir():
            out.append(
                Finding(
                    "note",
                    "lang.tests",
                    "no tests/ directory",
                    "tests/",
                    fix="Add tests/ and meson test() entries like the C family templates.",
                )
            )
        else:
            out.append(Finding("ok", "lang.tests", "tests/ present"))
    elif lang == "python":
        if (root / "tests").is_dir():
            out.append(Finding("ok", "lang.python.tests", "tests/ present"))
        else:
            out.append(
                Finding(
                    "warn",
                    "lang.python.tests",
                    "no tests/ (python template uses unittest + meson test)",
                    "tests/",
                    fix="Add tests/test_*.py and meson test() with PYTHONPATH=src.",
                )
            )
    elif lang == "rust" and not (root / "Cargo.toml").is_file():
        out.append(
            Finding(
                "error",
                "lang.rust.cargo",
                "missing Cargo.toml",
                "Cargo.toml",
                fix="Rust zephyr projects keep Cargo.toml plus meson custom_target for the binary.",
            )
        )
    elif lang == "go" and not (root / "go.mod").is_file():
        out.append(
            Finding(
                "error",
                "lang.go.mod",
                "missing go.mod",
                "go.mod",
                fix="Add go.mod; meson should `go build` with -X main.buildVersion from meson.project_version().",
            )
        )
    return out


def check_template_gaps(root: Path, lang: str, role: str) -> list[Finding]:
    """Warn about structural files the language template has that this tree lacks."""
    if role == "meta" or lang not in LANGS:
        return []
    try:
        tmpl = template_dir(lang)
    except SystemExit:
        return []
    if tmpl.resolve() == root.resolve():
        return []
    skip_top = {
        "build",
        "rpmbuild",
        ".git",
        "CLAUDE.md",
        ".cursor",
        ".vscode",
    }
    missing: list[str] = []
    for path in iter_files(tmpl):
        rel = path.relative_to(tmpl)
        if rel.parts and rel.parts[0] in skip_top:
            continue
        if TEMPLATE_PUFF in path.name or TEMPLATE_PUFF in rel.as_posix():
            continue
        if not (root / rel).exists():
            # only flag well-known scaffolding, not every po locale
            if rel.parts[0] in {"debian", "docs", "src", "tests", "rpm", ".githooks"} or rel.name in {
                "meson.build",
                "LICENSE",
                "README.md",
                "README-zh.md",
                "VERSION",
            }:
                missing.append(rel.as_posix())
    if not missing:
        return [Finding("ok", "template.coverage", "structural files from the language template are present")]
    preview = ", ".join(missing[:12])
    more = "" if len(missing) <= 12 else f" (+{len(missing) - 12} more)"
    return [
        Finding(
            "note",
            "template.coverage",
            f"language template {lang} has extra scaffolding not in this tree: {preview}{more}",
            fix=f"Compare with the {lang} template under pkgdatadir. Copy missing debian/docs/src/rpm "
            "files, or `zfr add` puffs. Do not copy build/ or debian leftover stamp files.",
        )
    ]


def collect_findings(root: Path) -> tuple[str, str, str, list[Finding]]:
    role = _role(root)
    if role == "meta":
        lang = "meta"
    else:
        try:
            lang = detect_lang(root)
        except SystemExit:
            lang = "unknown"
    meson = _meson_project_fields(root)
    src, _, _ = _control(root)
    name = src.get("Source") or meson.get("name") or root.name
    findings: list[Finding] = []
    findings.extend(check_layout(root, lang, role))
    findings.extend(check_identity(root, lang, role))
    findings.extend(check_meson(root, lang))
    findings.extend(check_debian(root, lang, role))
    findings.extend(check_rpm(root, lang))
    findings.extend(check_readme(root, role))
    findings.extend(check_leftovers(root, role))
    findings.extend(check_lang_bits(root, lang))
    findings.extend(check_template_gaps(root, lang, role))
    return name, lang, role, findings


def _next_steps(findings: list[Finding]) -> list[str]:
    steps: list[str] = []
    seen: set[str] = set()
    for f in findings:
        if f.severity not in ("error", "warn") or not f.fix:
            continue
        key = f.code
        if key in seen:
            continue
        seen.add(key)
        loc = f.file or ""
        if f.line:
            loc = f"{loc}:{f.line}"
        prefix = f"{loc}: " if loc else ""
        parts = [ln.strip() for ln in f.fix.strip().splitlines() if ln.strip()]
        summary = parts[0]
        if len(parts) > 1 and len(summary) < 60:
            summary = f"{summary} {parts[1]}"
        steps.append(f"{prefix}{summary}")
        if len(steps) >= 12:
            break
    return steps


def format_report(
    root: Path,
    name: str,
    lang: str,
    role: str,
    findings: list[Finding],
    *,
    verbose: bool = False,
    quiet: bool = False,
    color: str = "auto",
) -> str:
    csr = Csr(color)
    counts = {k: 0 for k in ("error", "warn", "note", "ok")}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    failed = counts["error"] > 0
    status = "FAIL" if failed else "PASS"
    status_s = csr.sev("error" if failed else "ok", status)

    lines: list[str] = []
    head = csr.wrap("zfr lint", csr.bold)
    lines.append(
        f"{head}: {root}  name={name}  lang={lang}  role={role}"
    )
    lines.append(
        f"status: {status_s}  "
        f"{csr.sev('error', 'errors=' + str(counts['error']))}  "
        f"{csr.sev('warn', 'warnings=' + str(counts['warn']))}  "
        f"notes={counts['note']}"
    )
    if not quiet:
        role_hint = {
            "meta": "zephyr meta-repo (templates + CLI tools)",
            "template": "language template inside the meta-repo (placeholders like zephyr/some_puff1 are expected)",
            "app": "project instantiated from a language template (directory name must match meson/debian; no leftover zephyr/some_puff1 tokens)",
        }.get(role, role)
        lines.append(csr.wrap(f"role: {role_hint}", csr.dim))
        lines.append("")
        lines.append(csr.wrap("Zephyr style (finish the project to this contract)", csr.bold, csr.magenta))
        for item in (
            "License AGPL-3.0-or-later (meson license, debian/copyright AGPL-3+, rpm License).",
            "Build with Meson; debian/rules uses dh --buildsystem=meson --builddirectory=debian/build.",
            "project() version from `zfr version`; keep fallback v=\"0.0.0\" # FIXED TO 0.0.0, DO NOT MODIFY.",
            "Man pages: docs/*.adoc + asciidoctor -b manpage; install bash-completion.",
            "Packaging: debian/control Build-Depends meson, ninja-build, asciidoctor; optional rpm/ aligned with debian.",
            "Apps: `zfr rename <dir>` then `zfr add <puff>`; VERSION matches debian/changelog (git describe may differ).",
        ):
            lines.append(f"  - {item}")
    lines.append("")

    order = {"error": 0, "warn": 1, "note": 2, "ok": 3}
    shown = [f for f in findings if f.severity != "ok" or verbose]
    if quiet:
        shown = [f for f in shown if f.severity == "error"]
    shown.sort(key=lambda f: (order.get(f.severity, 9), f.file or "", f.line or 0, f.code))

    for f in shown:
        loc = f.file or ""
        if f.line:
            loc = f"{loc}:{f.line}"
        tag = csr.sev(f.severity, f"{f.severity:5}")
        code = csr.wrap(f.code, csr.dim)
        loc_s = csr.wrap(loc, csr.bold, csr.blue) if loc else ""
        extra = f"  {loc_s}" if loc_s else ""
        lines.append(f"{tag}  {code}{extra}")
        lines.append(f"      {f.message}")
        if f.fix:
            for i, fl in enumerate(f.fix.strip().splitlines()):
                prefix = "      fix: " if i == 0 else "           "
                lines.append(csr.wrap(prefix + fl, csr.dim))
        lines.append("")

    steps = _next_steps(findings)
    if not quiet:
        if steps:
            lines.append(csr.wrap("Next steps (zephyr style)", csr.bold, csr.magenta))
            for i, step in enumerate(steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")
        lines.append(
            csr.wrap(
                "Hint: after edits, re-run `zfr lint` from the project (or a subdirectory). "
                "`zfr about -d -r` dumps packaging fields. Version for Meson/RPM is `zfr version`. "
                "`zfr ize` applies missing debian/rpm/meson/man/version-subst upgrades.",
                csr.dim,
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def cmd_lint(
    *,
    verbose: bool = False,
    quiet: bool = False,
    color: str = "auto",
    strict: bool = False,
    workdir: Path | None = None,
) -> int:
    root = find_project_dir(workdir)
    name, lang, role, findings = collect_findings(root)
    sys.stdout.write(
        format_report(
            root, name, lang, role, findings, verbose=verbose, quiet=quiet, color=color
        )
    )
    sys.stdout.flush()
    errors = sum(1 for f in findings if f.severity == "error")
    warns = sum(1 for f in findings if f.severity == "warn")
    if errors:
        return 1
    if strict and warns:
        return 1
    return 0
