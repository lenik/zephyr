# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr create / rename / add / remove command implementations."""

from __future__ import annotations

import re
import shutil
import subprocess
from email.utils import formatdate
from pathlib import Path

from . import (
    LANGS,
    TEMPLATE_PUFF,
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
    replacement_pairs,
    rewrite_tree,
    template_dir,
)
from .lang import puff_source_paths as _puff_source_paths_impl
from .lang import wire_add as _lang_wire_add
from .lang import wire_remove as _lang_wire_remove


def _puff_source_paths(lang: str, tmpl: Path) -> list[Path]:
    """Files/dirs in the template that belong to the example puff."""
    stem = TEMPLATE_PUFF
    pascal = case_variants(stem)["pascal"]
    return _puff_source_paths_impl(lang, tmpl, stem, pascal)


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


def _wire_add(lang: str, workdir: Path, name: str) -> None:
    _lang_wire_add(lang, workdir, name)


def _wire_remove(lang: str, workdir: Path, name: str) -> None:
    _lang_wire_remove(lang, workdir, name)
    meson = workdir / "meson.build"
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
