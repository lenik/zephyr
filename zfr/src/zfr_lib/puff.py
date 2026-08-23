# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr create / rename / add / remove command implementations."""

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
    instantiation_pairs,
    is_probably_text,
    iter_files,
    pkgdatadir,
    project_version,
    relative_to,
    remove_meson_list_entry,
    replacement_pairs,
    rewrite_tree,
    template_dir,
)
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
    elif lang == "cpp":
        candidates += [
            tmpl / "src" / f"{stem}.cpp",
            tmpl / "tests" / f"{stem}_test.cpp",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
        ]
    elif lang == "cpplib":
        candidates += [
            tmpl / "src" / f"{stem}.cpp",
            tmpl / "src" / f"{stem}.hpp",
            tmpl / "tests" / f"{stem}_test.cpp",
            tmpl / f"{stem}.bash",
            tmpl / "docs" / f"{stem}.adoc",
            tmpl / "po" / f"{stem}.pot",
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
    elif lang == "ruby":
        candidates += [
            tmpl / "src" / f"{stem}.rb",
            tmpl / "src" / "common_lib.rb",
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
        candidates += [
            tmpl / "src" / "main.rs",
            tmpl / "src" / "lib.rs",
            tmpl / "build-aux" / "cargo-build.sh",
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
    elif lang == "cpp" and meson.is_file():
        append_meson_list_entry(meson, "app_sources", f"src/{name}.cpp")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            append_meson_list_entry(tests_meson, "test_sources", f"{name}_test.cpp")
        _append_man_custom_target(meson, name)
    elif lang == "cpplib" and meson.is_file():
        append_meson_list_entry(meson, "app_sources", f"src/{name}.cpp")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            append_meson_list_entry(tests_meson, "test_sources", f"{name}_test.cpp")
        _append_man_custom_target(meson, name)
    elif lang == "bash" and meson.is_file():
        append_meson_list_entry(meson, "app_scripts", f"src/{name}.in")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        _append_man_custom_target(meson, name)
    elif lang == "perl" and meson.is_file():
        append_meson_list_entry(meson, "app_scripts", f"src/{name}.pl")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        _append_man_custom_target(meson, name)
    elif lang == "ruby" and meson.is_file():
        append_meson_list_entry(meson, "app_scripts", f"src/{name}.rb")
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
    elif lang == "cpp" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.cpp")
        remove_meson_list_entry(meson, f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            remove_meson_list_entry(tests_meson, f"{name}_test.cpp")
        _strip_man_custom_target(meson, name)
    elif lang == "cpplib" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.cpp")
        remove_meson_list_entry(meson, f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            remove_meson_list_entry(tests_meson, f"{name}_test.cpp")
        _strip_man_custom_target(meson, name)
    elif lang == "bash" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.in")
        remove_meson_list_entry(meson, f"{name}.bash")
        _strip_man_custom_target(meson, name)
    elif lang == "perl" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.pl")
        remove_meson_list_entry(meson, f"{name}.bash")
        _strip_man_custom_target(meson, name)
    elif lang == "ruby" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.rb")
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


_TEMPLATE_LEFTOVER_RE = re.compile(r"puff1|zephyr", re.IGNORECASE)


def _leftover_template_lines(root: Path) -> list[str]:
    """Paths that still match ``puff1`` or ``zephyr`` (same as grep -iE)."""
    hits: list[str] = []
    for path in iter_files(root):
        rel = path.relative_to(root)
        if _TEMPLATE_LEFTOVER_RE.search(path.name):
            hits.append(f"{rel}")
        if not path.is_file() or not is_probably_text(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if _TEMPLATE_LEFTOVER_RE.search(line):
                hits.append(f"{rel}:{i}:{line.strip()}")
    return hits


def _tree_mentions_puff(root: Path, stem: str) -> bool:
    """True if any path name or text file still contains the puff stem tokens."""
    variants = case_variants(stem)
    keys = [k for k in (variants["lower"], variants["upper"], variants["pascal"]) if k]
    for path in iter_files(root):
        if any(k in path.name for k in keys):
            return True
        if not path.is_file():
            continue
        try:
            if not is_probably_text(path):
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(k in text for k in keys):
            return True
    return False


def _add_one(name: str, workdir: Path | None = None) -> None:
    root = (workdir or Path.cwd()).resolve()
    lang = detect_lang(root)
    tmpl = template_dir(lang)
    pairs = instantiation_pairs(root.name, name)

    # If the template puff is still in the tree, rename it in place so all
    # tokens are substituted (needed for rust/java/haskell single-entry apps
    # where copying main.rs would skip an existing file).
    if _tree_mentions_puff(root, TEMPLATE_PUFF):
        print(f"add {name}: rename template {TEMPLATE_PUFF} → {name} (lang={lang})")
        files, renames = rewrite_tree(root, pairs, rename_paths=True)
        print(f"  {files} file(s) rewritten, {renames} path(s) renamed")
        _wire_add(lang, root, name)
        print("done")
        return

    sources = _puff_source_paths(lang, tmpl)
    if not sources:
        raise SystemExit(f"no puff template files found for language {lang!r} in {tmpl}")

    # Entrypoints that must be refreshed from the template (empty create may
    # have scrubbed some_puff1 → <package> but left main.rs in place).
    overwrite_names = {
        "main.rs",
        "Main.java",
        "Main.hs",
        "main.swift",
        "main.go",
    }

    print(f"add {name} (lang={lang}, template={tmpl})")
    for src in sources:
        if src.is_dir():
            for path in iter_files(src):
                dest = _dest_for(path, tmpl, root, pairs)
                if dest.exists() and path.name not in overwrite_names and TEMPLATE_PUFF not in path.name:
                    print(f"  skip exists: {dest.relative_to(root)}")
                    continue
                copy_renamed_file(path, dest, pairs)
                mark = "~" if dest.exists() else "+"
                # dest always exists after copy; detect prior existence:
                print(f"  {mark} {dest.relative_to(root)}")
        else:
            dest = _dest_for(src, tmpl, root, pairs)
            existed = dest.exists()
            if existed and src.name not in overwrite_names and TEMPLATE_PUFF not in src.name:
                print(f"  skip exists: {dest.relative_to(root)}")
                continue
            copy_renamed_file(src, dest, pairs)
            print(f"  {'~' if existed else '+'} {dest.relative_to(root)}")

    if lang == "rust":
        _rust_set_bin_names(root, name)

    files, renames = rewrite_tree(root, pairs, rename_paths=True)
    if files or renames:
        print(f"  rewrite remaining: {files} file(s), {renames} path(s)")

    _wire_add(lang, root, name)
    print("done")


def _rust_set_bin_names(root: Path, name: str) -> None:
    """Set [package] name and [[bin]] name in Cargo.toml to the puff name."""
    cargo = root / "Cargo.toml"
    if not cargo.is_file():
        return
    text = cargo.read_text(encoding="utf-8")
    new = re.sub(r'(?m)^name = "[^"]+"', f'name = "{name}"', text, count=1)
    new = re.sub(
        r'(?ms)(\[\[bin\]\]\s*\nname = ")[^"]+(")',
        rf"\1{name}\2",
        new,
    )
    if new != text:
        cargo.write_text(new, encoding="utf-8")
        print(f"  ~ Cargo.toml ([package]/[[bin]] → {name})")

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
