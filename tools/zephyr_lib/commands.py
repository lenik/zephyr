# SPDX-License-Identifier: AGPL-3.0-or-later
"""zephyr create / rename / add / remove command implementations."""

from __future__ import annotations

import re
import shutil
import subprocess
import uuid
from email.utils import formatdate
from pathlib import Path

from . import (
    LANGS,
    TEMPLATE_PUFF,
    append_meson_list_entry,
    apply_name_replacements,
    case_variants,
    copy_renamed_file,
    detect_lang,
    iter_files,
    relative_to,
    remove_meson_list_entry,
    replacement_pairs,
    rewrite_tree,
    template_dir,
)

DEFAULT_DISTRIBUTION = "unstable"
DEFAULT_INIT_VERSION = "0.0.1"
DEFAULT_AUTHOR = "Lenik (谢继雷)"
DEFAULT_EMAIL = "lenik@bodz.net"

_COPY_IGNORE = shutil.ignore_patterns(
    ".cache",
    ".cursor",
    ".git",
    ".hg",
    ".svn",
    ".vscode",
    "__pycache__",
    "bin",
    "build",
    "cargo-target",
    "dist",
    "meson-info",
    "meson-logs",
    "meson-private",
    "node_modules",
    "obj",
    "target",
    "CLAUDE.md",
    "*.pyc",
)


def _write_debian_changelog(
    dest: Path,
    *,
    package: str,
    version: str,
    distribution: str,
    author: str,
    email: str,
) -> None:
    """Write a fresh debian/changelog (template changelog is omitted on create)."""
    deb_dir = dest / "debian"
    deb_dir.mkdir(parents=True, exist_ok=True)
    stamp = formatdate(localtime=True)
    text = (
        f"{package} ({version}) {distribution}; urgency=medium\n"
        f"\n"
        f"  * Initial release\n"
        f"\n"
        f" -- {author} <{email}>  {stamp}\n"
    )
    (deb_dir / "changelog").write_text(text, encoding="utf-8")


def _git_init_commit_tag(
    dest: Path,
    *,
    version: str,
    author: str,
    email: str,
) -> None:
    """Initialize git, create the first commit, and tag vVERSION."""
    def run(args: list[str]) -> None:
        subprocess.run(args, cwd=dest, check=True, capture_output=True, text=True)

    # Identity via -c only (do not write git config).
    ident = ["-c", f"user.name={author}", "-c", f"user.email={email}"]

    run(["git", "init"])
    run(["git", "add", "-A"])
    ver = version.lstrip("v")
    msg = f"Initial release {ver}\n"
    run(["git", *ident, "commit", "-m", msg])
    tag = f"v{ver}"
    run(["git", *ident, "tag", "-a", tag, "-m", f"{tag}: initial release"])


def cmd_create(
    project_name: str,
    lang: str = "python",
    puff_names: list[str] | None = None,
    workdir: Path | None = None,
    *,
    distribution: str = DEFAULT_DISTRIBUTION,
    init_version: str = DEFAULT_INIT_VERSION,
    author: str = DEFAULT_AUTHOR,
    email: str = DEFAULT_EMAIL,
) -> None:
    """Copy a language template into ./<project_name>/ and rename the project."""
    root = (workdir or Path.cwd()).resolve()
    dest = root / project_name
    if dest.exists():
        raise SystemExit(f"destination already exists: {dest}")

    lang = lang.lower().strip()
    if lang not in LANGS:
        raise SystemExit(
            f"unknown language {lang!r}; supported: {', '.join(LANGS)}"
        )

    tmpl = template_dir(lang)
    print(f"create {project_name} (lang={lang}, template={tmpl})")
    shutil.copytree(tmpl, dest, ignore=_COPY_IGNORE)

    # Never keep the template changelog; regenerate below.
    changelog = dest / "debian" / "changelog"
    if changelog.is_file():
        changelog.unlink()

    print(f"rename zephyr → {project_name}")
    pairs = replacement_pairs("zephyr", project_name)
    files, renames = rewrite_tree(dest, pairs, rename_paths=True)
    print(f"  project: {files} file(s) rewritten, {renames} path(s) renamed")

    # Drop the template example puff so the new project starts empty by default.
    cmd_remove([TEMPLATE_PUFF], workdir=dest)

    for name in puff_names or []:
        cmd_add([name], workdir=dest)

    print(
        f"debian/changelog ← {project_name} ({init_version}) {distribution} "
        f"({author} <{email}>)"
    )
    _write_debian_changelog(
        dest,
        package=project_name,
        version=init_version,
        distribution=distribution,
        author=author,
        email=email,
    )

    print(f"git init + commit + tag v{init_version.lstrip('v')}")
    try:
        _git_init_commit_tag(
            dest,
            version=init_version,
            author=author,
            email=email,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        raise SystemExit(f"git init/commit/tag failed: {err}") from e

    print(f"created {dest}")


def cmd_rename(project_name: str, examples: list[str], workdir: Path | None = None) -> None:
    root = (workdir or Path.cwd()).resolve()
    print(f"rename zephyr → {project_name}")
    pairs = replacement_pairs("zephyr", project_name)
    files, renames = rewrite_tree(root, pairs, rename_paths=True)
    print(f"  project: {files} file(s) rewritten, {renames} path(s) renamed")

    for ex in examples:
        print(f"rename example {TEMPLATE_PUFF} → {ex}")
        pairs = replacement_pairs(TEMPLATE_PUFF, ex)
        files, renames = rewrite_tree(root, pairs, rename_paths=True)
        print(f"  example: {files} file(s) rewritten, {renames} path(s) renamed")


def _puff_source_paths(lang: str, tmpl: Path) -> list[Path]:
    """Files/dirs in the template that belong to the example puff."""
    stem = TEMPLATE_PUFF
    pascal = case_variants(stem)["pascal"]
    found: list[Path] = []

    candidates: list[Path] = []
    if lang == "clib":
        candidates += [
            tmpl / "src" / f"{stem}.c",
            tmpl / "src" / f"{stem}.h",
            tmpl / "tests" / f"{stem}_test.c",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "c":
        candidates += [
            tmpl / "src" / f"{stem}.c",
            tmpl / "tests" / f"{stem}_test.c",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
        ]
    elif lang == "bash":
        candidates += [
            tmpl / "src" / f"{stem}.in",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
        ]
    elif lang == "perl":
        candidates += [
            tmpl / "src" / f"{stem}.pl",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
        ]
    elif lang == "python":
        candidates += [
            tmpl / "src" / f"{stem}.py",
            tmpl / "tests" / f"test_{stem}.py",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "go":
        cmd = tmpl / "cmd" / stem
        if cmd.is_dir():
            found.append(cmd)
        candidates += [
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "csharp":
        app = tmpl / "apps" / stem
        if app.is_dir():
            found.append(app)
        candidates += [
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
        ]
    elif lang == "rust":
        # Single-bin crate: cloning a second bin needs Cargo.toml edits; still
        # ship the man/bash/pot scaffolds and main.rs as a starting point.
        candidates += [
            tmpl / "src" / "main.rs",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "java":
        candidates += [
            tmpl / "src" / "Main.java",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "erlang":
        candidates += [
            tmpl / "src" / f"{stem}.erl",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "smalltalk":
        candidates += [
            tmpl / "src" / f"{stem}.st",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "typescript":
        candidates += [
            tmpl / "src" / f"{stem}.ts",
            tmpl / "src" / f"{stem}.sh.in",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / f"{stem}.bash",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang in ("haskell", "swift"):
        # Entry is Main.hs / main.swift — copy man/bash/pot and note meson wiring.
        candidates += [
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
        ]
        if lang == "haskell":
            candidates.append(tmpl / "src" / "Main.hs")
        else:
            candidates.append(tmpl / "src" / "main.swift")
    else:
        # Generic: anything named after the stem.
        for path in iter_files(tmpl):
            if stem in path.name or pascal in path.name:
                candidates.append(path)

    for c in candidates:
        if c.exists():
            found.append(c)
    # Unique while preserving order
    out: list[Path] = []
    seen: set[Path] = set()
    for p in found:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return out


def _dest_for(src: Path, tmpl: Path, dest_root: Path, pairs: list[tuple[str, str]]) -> Path:
    rel = relative_to(src, tmpl)
    parts = [apply_name_replacements(part, pairs) for part in rel.parts]
    return dest_root.joinpath(*parts)


def _scrub_meson_hardcoded_puff(meson: Path, name: str, project_name: str | None = None) -> None:
    """Remove stale hardcoded puff refs (symlink helpers); retarget pot paths."""
    if not meson.is_file():
        return
    text = meson.read_text(encoding="utf-8")
    variants = case_variants(name)
    keys = sorted(
        {k for k in (variants["lower"], variants["upper"], variants["pascal"]) if k},
        key=len,
        reverse=True,
    )
    if not keys:
        return
    token_re = re.compile(
        r"(^|[^A-Za-z0-9])(?:" + "|".join(re.escape(k) for k in keys) + r")([^A-Za-z0-9]|$)"
    )

    def _is_symlink_helper_line(line: str) -> bool:
        if token_re.search(line) is None:
            return False
        if "ln -sfn" in line:
            return True
        if "/bash-completion/completions/" in line:
            return True
        if "mandir/man1/" in line or "$mandir/man1/" in line:
            return True
        if "$bindir/" in line or '"$bindir/' in line or "'$bindir/" in line:
            return True
        for k in keys:
            if f"@1@/{k}" in line or f"@3@/man1/{k}" in line:
                return True
            if f"@2@/bash-completion/" in line and k in line:
                return True
        return False

    out: list[str] = []
    for line in text.splitlines(keepends=True):
        if not _is_symlink_helper_line(line):
            out.append(line)
            continue
        # Keep a valid empty loop header when removing the path list.
        if "for p in" in line:
            indent = re.match(r"[ \t]*", line).group(0)
            if re.search(r"\bdo\b", line):
                out.append(f"{indent}for p in; do\n")
            else:
                out.append(f"{indent}for p in;\n")
        # else: drop ln -sfn / path-continuation lines
    new = "".join(out)
    new = re.sub(r"for p in;\s*\n\s*do\b", "for p in; do", new)
    new = re.sub(r"for p in\s*\\\s*\n\s*do\b", "for p in; do", new)
    if project_name:
        for k in keys:
            new = new.replace(f"{k}.pot", f"{project_name}.pot")
    if new != text:
        meson.write_text(new, encoding="utf-8")



def _strip_man_custom_target(meson: Path, name: str) -> None:
    """Remove a hardcoded '{name}-man' custom_target block if present."""
    if not meson.is_file():
        return
    text = meson.read_text(encoding="utf-8")
    new = re.sub(
        rf"\n?custom_target\(\n\s*'{re.escape(name)}-man',\n(?:.*?\n)*?\)\n",
        "\n",
        text,
        count=1,
    )
    if new != text:
        meson.write_text(new, encoding="utf-8")


def _append_man_custom_target(meson: Path, name: str) -> None:
    """Append a man-page custom_target for docs/{name}.adoc when missing."""
    if not meson.is_file():
        return
    text = meson.read_text(encoding="utf-8")
    if f"'{name}-man'" in text:
        return
    if "asciidoctor" not in text:
        return
    block = f"""
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
    # Prefer before run_target / subdir('tests') / end of file.
    for marker in ("\nsubdir('tests')", "\nrun_target(", "\ntest("):
        idx = text.find(marker)
        if idx != -1:
            meson.write_text(text[:idx] + block + text[idx:], encoding="utf-8")
            return
    meson.write_text(text.rstrip() + "\n" + block, encoding="utf-8")


def _strip_python_meson_puff(meson: Path, name: str) -> None:
    """Remove hardcoded python custom_target / bash / man entries for a puff."""
    if not meson.is_file():
        return
    text = meson.read_text(encoding="utf-8")
    original = text
    text = re.sub(
        rf"\n?{re.escape(name)}_exe = custom_target\(\n(?:.*?\n)*?\)\n",
        "\n",
        text,
        count=1,
    )
    text = re.sub(
        rf"\n?install_data\(\n\s*'{re.escape(name)}\.bash',\n(?:.*?\n)*?\)\n",
        "\n",
        text,
        count=1,
    )
    if text != original:
        meson.write_text(text, encoding="utf-8")
    _strip_man_custom_target(meson, name)


def _wire_add(lang: str, workdir: Path, name: str) -> None:
    meson = workdir / "meson.build"
    if lang == "clib" and meson.is_file():
        append_meson_list_entry(meson, "app_sources", f"src/{name}.c")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            append_meson_list_entry(tests_meson, "test_sources", f"{name}_test.c")
        _append_man_custom_target(meson, name)
    elif lang == "c" and meson.is_file():
        append_meson_list_entry(meson, "app_sources", f"src/{name}.c")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            append_meson_list_entry(tests_meson, "test_sources", f"{name}_test.c")
        _append_man_custom_target(meson, name)
    elif lang == "bash" and meson.is_file():
        append_meson_list_entry(meson, "app_scripts", f"src/{name}.in")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        _append_man_custom_target(meson, name)
    elif lang == "perl" and meson.is_file():
        append_meson_list_entry(meson, "app_scripts", f"src/{name}.pl")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        _append_man_custom_target(meson, name)
    elif lang == "python" and meson.is_file():
        # Prefer documenting; python template hardcodes one custom_target.
        # Append a second custom_target block after the first if absent.
        text = meson.read_text(encoding="utf-8")
        if f"{name}_exe" not in text:
            block = f"""
{name}_exe = custom_target(
    '{name}',
    input: 'src/{name}.py',
    output: '{name}',
    command: [
        py,
        '-c',
        'import os, shutil, sys; shutil.copyfile(sys.argv[1], sys.argv[2]); os.chmod(sys.argv[2], 0o755)',
        '@INPUT@',
        '@OUTPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)
"""
            # Insert after first custom_target closing paren block of some_puff1/TEMPLATE
            marker = "install_dir: bindir,\n)\n"
            idx = text.find(marker)
            if idx != -1:
                idx = idx + len(marker)
                meson.write_text(text[:idx] + block + text[idx:], encoding="utf-8")
            else:
                # Empty project after create/remove: insert before common_lib or at end of
                # the early install section.
                insert_at = text.find("common_lib_mod = custom_target(")
                if insert_at == -1:
                    insert_at = text.find("install_data(")
                if insert_at == -1:
                    insert_at = len(text)
                meson.write_text(text[:insert_at] + block + "\n" + text[insert_at:], encoding="utf-8")
        text = meson.read_text(encoding="utf-8")
        if f"'{name}.bash'" not in text and f'"{name}.bash"' not in text:
            bash_block = f"""
install_data(
    '{name}.bash',
    install_dir: datadir / 'bash-completion' / 'completions',
    rename: '{name}',
)
"""
            # Insert before pkgdoc install_data if present.
            m = re.search(
                r"\ninstall_data\(\n\s*\[\n\s*'LICENSE'",
                text,
            )
            if m:
                meson.write_text(text[: m.start()] + bash_block + text[m.start() :], encoding="utf-8")
            else:
                meson.write_text(text + bash_block, encoding="utf-8")
        _append_man_custom_target(meson, name)
    elif lang == "go":
        # cmd/<name>/ is enough for `go build`; meson may still hardcode one target.
        pass
    elif lang == "csharp":
        sln = workdir / "zephyr.sln"
        if sln.is_file():
            pascal = case_variants(name)["pascal"]
            text = sln.read_text(encoding="utf-8")
            if pascal not in text:
                guid = "{" + str(uuid.uuid4()).upper() + "}"
                line = (
                    f'Project("{{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}}") = '
                    f'"{pascal}", "apps/{name}/{pascal}.csproj", "{guid}"\n'
                    f"EndProject\n"
                )
                # Insert before Global
                text = text.replace("\nGlobal\n", "\n" + line + "Global\n", 1)
                sln.write_text(text, encoding="utf-8")
        _append_man_custom_target(meson, name)


def _wire_remove(lang: str, workdir: Path, name: str) -> None:
    meson = workdir / "meson.build"
    if lang == "clib" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.c")
        remove_meson_list_entry(meson, f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            remove_meson_list_entry(tests_meson, f"{name}_test.c")
        _strip_man_custom_target(meson, name)
    elif lang == "c" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.c")
        remove_meson_list_entry(meson, f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            remove_meson_list_entry(tests_meson, f"{name}_test.c")
        _strip_man_custom_target(meson, name)
    elif lang == "bash" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.in")
        remove_meson_list_entry(meson, f"{name}.bash")
        _strip_man_custom_target(meson, name)
    elif lang == "perl" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.pl")
        remove_meson_list_entry(meson, f"{name}.bash")
        _strip_man_custom_target(meson, name)
    elif lang == "python" and meson.is_file():
        _strip_python_meson_puff(meson, name)
    elif lang == "csharp":
        sln = workdir / "zephyr.sln"
        if sln.is_file():
            pascal = case_variants(name)["pascal"]
            text = sln.read_text(encoding="utf-8")
            new = re.sub(
                rf'Project\("[^"]+"\) = "{re.escape(pascal)}".*?\nEndProject\n',
                "",
                text,
                flags=re.S,
            )
            if new != text:
                sln.write_text(new, encoding="utf-8")
        _strip_man_custom_target(meson, name)
    else:
        _strip_man_custom_target(meson, name)

    _scrub_meson_hardcoded_puff(meson, name, project_name=workdir.name)


def _normalize_names(names: str | list[str]) -> list[str]:
    if isinstance(names, str):
        return [names]
    return list(names)


def _add_one(name: str, workdir: Path | None = None) -> None:
    root = (workdir or Path.cwd()).resolve()
    lang = detect_lang(root)
    tmpl = template_dir(lang)
    pairs = replacement_pairs(TEMPLATE_PUFF, name)
    sources = _puff_source_paths(lang, tmpl)
    if not sources:
        raise SystemExit(f"no puff template files found for language {lang!r} in {tmpl}")

    print(f"add {name} (lang={lang}, template={tmpl})")
    for src in sources:
        if src.is_dir():
            for path in iter_files(src):
                dest = _dest_for(path, tmpl, root, pairs)
                if dest.exists():
                    print(f"  skip exists: {dest.relative_to(root)}")
                    continue
                copy_renamed_file(path, dest, pairs)
                print(f"  + {dest.relative_to(root)}")
        else:
            dest = _dest_for(src, tmpl, root, pairs)
            if dest.exists():
                print(f"  skip exists: {dest.relative_to(root)}")
                continue
            copy_renamed_file(src, dest, pairs)
            print(f"  + {dest.relative_to(root)}")

    _wire_add(lang, root, name)
    print("done")


def cmd_add(names: str | list[str], workdir: Path | None = None) -> None:
    for name in _normalize_names(names):
        _add_one(name, workdir=workdir)


def _filename_matches_puff(filename: str, name: str) -> bool:
    """True if filename contains puff name as a whole token (not a substring)."""
    variants = case_variants(name)
    keys = [k for k in (variants["lower"], variants["upper"], variants["pascal"]) if k]
    # Longest first so Pascal wins over accidental shorter forms.
    keys = sorted(set(keys), key=len, reverse=True)
    for k in keys:
        if re.search(
            rf"(^|[^A-Za-z0-9]){re.escape(k)}([^A-Za-z0-9]|$)",
            filename,
        ):
            return True
    return False


def _collect_puff_paths(workdir: Path, name: str) -> list[Path]:
    variants = case_variants(name)
    found: list[Path] = []
    for path in iter_files(workdir):
        if _filename_matches_puff(path.name, name):
            found.append(path)
    # Also known dirs
    for rel in (f"cmd/{name}", f"apps/{name}", f"apps/{variants['pascal']}"):
        p = workdir / rel
        if p.is_dir():
            found.append(p)
    # Unique
    out: list[Path] = []
    seen: set[Path] = set()
    for p in found:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return out


def _remove_one(name: str, workdir: Path | None = None) -> None:
    root = (workdir or Path.cwd()).resolve()
    lang = detect_lang(root)
    paths = _collect_puff_paths(root, name)
    if not paths:
        raise SystemExit(f"no files found for puff {name!r} in {root}")

    print(f"remove {name} (lang={lang})")
    # Delete files first, then dirs (deepest first)
    files = [p for p in paths if p.is_file()]
    dirs = [p for p in paths if p.is_dir()]
    dirs.sort(key=lambda p: len(str(p)), reverse=True)
    for p in files:
        p.unlink(missing_ok=True)
        try:
            print(f"  - {p.relative_to(root)}")
        except ValueError:
            print(f"  - {p}")
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)
        try:
            print(f"  - {d.relative_to(root)}/")
        except ValueError:
            print(f"  - {d}/")

    _wire_remove(lang, root, name)
    print("done")


def cmd_remove(names: str | list[str], workdir: Path | None = None) -> None:
    for name in _normalize_names(names):
        _remove_one(name, workdir=workdir)
