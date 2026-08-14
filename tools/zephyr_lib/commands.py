# SPDX-License-Identifier: AGPL-3.0-or-later
"""zephyr rename / add / remove command implementations."""

from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from . import (
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
    if lang == "c":
        candidates += [
            tmpl / "src" / f"{stem}.c",
            tmpl / "src" / f"{stem}.h",
            tmpl / "tests" / f"{stem}_test.c",
            tmpl / f"{stem}.bash",
            tmpl / f"{stem}.1.in",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "python":
        candidates += [
            tmpl / "src" / f"{stem}.py",
            tmpl / "tests" / f"test_{stem}.py",
            tmpl / f"{stem}.bash",
            tmpl / f"{stem}.1.in",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "go":
        cmd = tmpl / "cmd" / stem
        if cmd.is_dir():
            found.append(cmd)
        candidates += [
            tmpl / f"{stem}.bash",
            tmpl / f"{stem}.1.in",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "cs":
        app = tmpl / "apps" / stem
        if app.is_dir():
            found.append(app)
        candidates += [
            tmpl / f"{stem}.bash",
            tmpl / f"{stem}.1.in",
        ]
    elif lang == "rust":
        # Single-bin crate: cloning a second bin needs Cargo.toml edits; still
        # ship the man/bash/pot scaffolds and main.rs as a starting point.
        candidates += [
            tmpl / "src" / "main.rs",
            tmpl / f"{stem}.bash",
            tmpl / f"{stem}.1.in",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "java":
        candidates += [
            tmpl / "src" / "Main.java",
            tmpl / f"{stem}.bash",
            tmpl / f"{stem}.1.in",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "erlang":
        candidates += [
            tmpl / "src" / f"{stem}.erl",
            tmpl / f"{stem}.bash",
            tmpl / f"{stem}.1.in",
            tmpl / "po" / f"{stem}.pot",
        ]
    elif lang == "smalltalk":
        candidates += [
            tmpl / "src" / f"{stem}.st",
            tmpl / f"{stem}.bash",
            tmpl / f"{stem}.1.in",
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
            tmpl / f"{stem}.1.in",
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


def _wire_add(lang: str, workdir: Path, name: str) -> None:
    meson = workdir / "meson.build"
    if lang == "c" and meson.is_file():
        append_meson_list_entry(meson, "app_sources", f"src/{name}.c")
        append_meson_list_entry(meson, "bash_files", f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            append_meson_list_entry(tests_meson, "test_sources", f"{name}_test.c")
    elif lang == "python" and meson.is_file():
        # Prefer documenting; python template hardcodes one custom_target.
        # Append a second custom_target block after the first if absent.
        text = meson.read_text(encoding="utf-8")
        if f"'{name}'" not in text and "custom_target(" in text:
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
    elif lang == "go":
        # cmd/<name>/ is enough for `go build`; meson may still hardcode one target.
        pass
    elif lang == "cs":
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


def _wire_remove(lang: str, workdir: Path, name: str) -> None:
    meson = workdir / "meson.build"
    if lang == "c" and meson.is_file():
        remove_meson_list_entry(meson, f"src/{name}.c")
        remove_meson_list_entry(meson, f"{name}.bash")
        tests_meson = workdir / "tests" / "meson.build"
        if tests_meson.is_file():
            remove_meson_list_entry(tests_meson, f"{name}_test.c")
    elif lang == "cs":
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


def cmd_add(name: str, workdir: Path | None = None) -> None:
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


def _collect_puff_paths(workdir: Path, name: str) -> list[Path]:
    variants = case_variants(name)
    keys = {variants["lower"], variants["upper"], variants["pascal"]}
    found: list[Path] = []
    for path in iter_files(workdir):
        if any(k in path.name for k in keys if k):
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


def cmd_remove(name: str, workdir: Path | None = None) -> None:
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
