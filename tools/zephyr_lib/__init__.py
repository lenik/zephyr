# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared helpers for the zephyr CLI tools."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable

# Placeholder example app name shipped in templates.
TEMPLATE_PUFF = "some_puff1"

LANGS = (
    "c",
    "cs",
    "erlang",
    "go",
    "haskell",
    "java",
    "python",
    "rust",
    "smalltalk",
    "swift",
    "typescript",
)

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".cursor",
    ".vscode",
    "build",
    "debian",
    "dist",
    "node_modules",
    "bin",
    "obj",
    "target",
    "cargo-target",
    "__pycache__",
    "meson-info",
    "meson-logs",
    "meson-private",
}


def snake_to_pascal(name: str) -> str:
    parts = re.split(r"[_\-]+", name)
    return "".join(p[:1].upper() + p[1:] if p else "" for p in parts)


def case_variants(name: str) -> dict[str, str]:
    """Return lower / UPPER / Pascal forms for a snake_case-ish identifier."""
    lower = name
    upper = re.sub(r"[_\-]+", "_", name).upper()
    pascal = snake_to_pascal(name)
    return {"lower": lower, "upper": upper, "pascal": pascal}


def replacement_pairs(old: str, new: str) -> list[tuple[str, str]]:
    """Ordered (old, new) pairs for content/path rewriting (longest first)."""
    o = case_variants(old)
    n = case_variants(new)
    pairs = [
        (o["upper"], n["upper"]),
        (o["pascal"], n["pascal"]),
        (o["lower"], n["lower"]),
    ]
    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for a, b in pairs:
        if a in seen or a == b:
            continue
        seen.add(a)
        out.append((a, b))
    return out


def apply_text_replacements(text: str, pairs: Iterable[tuple[str, str]]) -> str:
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def apply_name_replacements(name: str, pairs: Iterable[tuple[str, str]]) -> str:
    for old, new in pairs:
        if old in name:
            name = name.replace(old, new)
    return name


def pkgdatadir() -> Path:
    env = os.environ.get("ZEPHYR_PKGDATADIR")
    if env:
        return Path(env)

    try:
        from . import paths_config  # type: ignore

        return Path(paths_config.PKGDATADIR)
    except Exception:
        pass

    here = Path(__file__).resolve()
    # tools/zephyr_lib → repo root when running from the source tree
    source_root = here.parents[2] if here.parent.name == "zephyr_lib" else here.parents[1]
    if (source_root / "c" / "meson.build").is_file() and (
        source_root / "python" / "meson.build"
    ).is_file():
        return source_root

    for base in (Path(sys.prefix), Path("/usr"), Path("/usr/local")):
        cand = base / "share" / "zephyr"
        if cand.is_dir():
            return cand

    return source_root


def template_dir(lang: str) -> Path:
    root = pkgdatadir()
    path = root / lang
    if not path.is_dir():
        raise SystemExit(f"template not found for language {lang!r}: {path}")
    return path


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        dirnames[:] = [
            d
            for d in dirnames
            if d not in SKIP_DIR_NAMES and not d.startswith(".")
        ]
        for fn in filenames:
            yield p / fn


def is_probably_text(path: Path) -> bool:
    try:
        data = path.read_bytes()[:8192]
    except OSError:
        return False
    if b"\0" in data:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def rewrite_tree(
    root: Path,
    pairs: list[tuple[str, str]],
    *,
    rename_paths: bool = True,
) -> tuple[int, int]:
    """Rewrite file contents and optionally rename paths under root."""
    files_changed = 0
    for path in list(iter_files(root)):
        if not is_probably_text(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new = apply_text_replacements(text, pairs)
        if new != text:
            path.write_text(new, encoding="utf-8")
            files_changed += 1

    renamed = 0
    if rename_paths:
        paths: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            p = Path(dirpath)
            if any(part in SKIP_DIR_NAMES for part in p.parts):
                continue
            for fn in filenames:
                paths.append(p / fn)
            if p != root:
                paths.append(p)
        paths.sort(key=lambda x: len(str(x)), reverse=True)
        for path in paths:
            new_name = apply_name_replacements(path.name, pairs)
            if new_name == path.name:
                continue
            dest = path.with_name(new_name)
            if dest.exists():
                continue
            path.rename(dest)
            renamed += 1
    return files_changed, renamed


def _is_zephyr_meta_repo(root: Path) -> bool:
    """True if root is the multi-language zephyr template meta-repo."""
    present = [lang for lang in ("c", "python", "rust") if (root / lang).is_dir()]
    if len(present) < 2:
        return False
    meson = root / "meson.build"
    if not meson.is_file():
        return False
    txt = meson.read_text(encoding="utf-8", errors="ignore")
    # Top-level meson installs language templates via template_langs / install_subdir.
    if "template_langs" in txt:
        return True
    if "install_subdir" in txt and any(
        re.search(rf"install_subdir\s*\(\s*['\"]{re.escape(lang)}['\"]", txt)
        or f"'{lang}'" in txt
        for lang in LANGS
    ):
        # Heuristic: foreach lang : template_langs / install_subdir(lang, ...)
        if "foreach lang" in txt or "pkgdatadir" in txt:
            return True
    # Multiple language template dirs plus tools/zephyr CLI.
    if (root / "tools" / "zephyr").is_file() and sum(
        1 for lang in LANGS if (root / lang / "meson.build").is_file()
    ) >= 3:
        return True
    return False


def _shallow_source_dirs(root: Path) -> list[Path]:
    """Project dirs to scan for sources — never sibling language templates."""
    dirs = [root]
    for name in ("src", "cmd", "apps", "tests"):
        p = root / name
        if p.is_dir():
            dirs.append(p)
    return dirs


def _has_ext_shallow(root: Path, *exts: str) -> bool:
    """True if any file with one of exts exists under shallow project dirs."""
    want = {e.lower() for e in exts}
    for base in _shallow_source_dirs(root):
        if base == root:
            for path in root.iterdir():
                if path.is_file() and path.suffix.lower() in want:
                    return True
            continue
        for path in iter_files(base):
            if path.suffix.lower() in want:
                return True
    return False


def _cs_project_markers(root: Path) -> bool:
    if (root / "zephyr.sln").is_file() or any(root.glob("*.csproj")):
        return True
    apps = root / "apps"
    if apps.is_dir():
        if any(apps.glob("*.csproj")) or any(apps.glob("*/*.csproj")):
            return True
    return False


def detect_lang(workdir: Path | None = None) -> str:
    """Detect zephyr template language from project files in workdir."""
    root = (workdir or Path.cwd()).resolve()

    if _is_zephyr_meta_repo(root):
        raise SystemExit(
            f"{root} looks like the zephyr meta-repo root "
            "(multiple language templates). "
            "Run zephyr from a language project directory "
            "(e.g. c/, python/, rust/), not the repository root."
        )

    meson = root / "meson.build"
    meson_txt = meson.read_text(encoding="utf-8", errors="ignore") if meson.is_file() else ""
    meson_head = meson_txt[:1200]
    control = root / "debian" / "control"
    control_txt = control.read_text(encoding="utf-8", errors="ignore") if control.is_file() else ""
    # Prefer Build-Depends + Depends for language hints.
    control_deps = control_txt

    # --- Root markers (no tree walk) ---
    if (root / "go.mod").is_file():
        return "go"
    if (root / "Cargo.toml").is_file():
        return "rust"
    if (root / "package.json").is_file() and any(root.glob("tsconfig*.json")):
        return "typescript"
    if _cs_project_markers(root):
        return "cs"

    # meson project() language list and debian/control Depends / Build-Depends
    if meson.is_file():
        # project('name', 'c', 'cpp', ...) or project('name', 'rust', ...)
        m = re.search(r"project\s*\((.*?)\)", meson_head, re.S)
        if m:
            args = m.group(1)
            # Quoted language tokens after the project name.
            langs_in_project = [
                x.lower()
                for x in re.findall(r"['\"]([A-Za-z+#]+)['\"]", args)
            ]
            # First string is usually the project name; rest may include languages.
            for tok in langs_in_project[1:]:
                if tok in ("c", "cpp", "c++"):
                    return "c"
                if tok == "rust":
                    return "rust"

    # debian control dependency hints (no source walk)
    dep_checks: list[tuple[str, re.Pattern[str]]] = [
        ("go", re.compile(r"\bgolang\b|\bgolang-go\b", re.I)),
        ("rust", re.compile(r"\bcargo\b|\brustc\b", re.I)),
        ("typescript", re.compile(r"\bnodejs\b|\bnpm\b|\bnode-typescript\b|\btypescript\b", re.I)),
        ("cs", re.compile(r"\bdotnet(?:-sdk)?\b", re.I)),
        ("java", re.compile(r"\bdefault-jdk\b|\bdefault-jre\b|\bjava-runtime\b|\bopenjdk\b", re.I)),
        ("python", re.compile(r"\bpython3?\b", re.I)),
        ("erlang", re.compile(r"\berlang\b", re.I)),
        ("haskell", re.compile(r"\bghc\b|\bhaskell\b", re.I)),
        ("smalltalk", re.compile(r"\bgnu-smalltalk\b|\bsmalltalk\b", re.I)),
        ("swift", re.compile(r"\bswiftlang\b|\bswift\b", re.I)),
        # C last among deps: libbas-c / check are weak alone; prefer explicit C toolchain.
        ("c", re.compile(r"\blibbas-c-dev\b|\bpkgconf\b.*\bcheck\b|\bcheck\b.*\bpkgconf\b", re.I)),
    ]
    if control_deps:
        for lang, pat in dep_checks:
            if pat.search(control_deps):
                # Avoid matching python3 from unrelated packages when stronger markers
                # already handled; still useful for language-only projects.
                if lang == "python" and not (
                    re.search(r"^Depends:\s*python3\b", control_deps, re.M | re.I)
                    or re.search(r"Build-Depends:.*\bpython3\b", control_deps, re.I)
                    or "import('python')" in meson_txt
                ):
                    continue
                if lang == "c" and re.search(
                    r"\bcargo\b|\brustc\b|\bgolang\b|\bpython3\b|\bdotnet\b|"
                    r"\berlang\b|\bghc\b|\bswift|\bnodejs\b|\bdefault-jdk\b|"
                    r"\bgnu-smalltalk\b",
                    control_deps,
                    re.I,
                ):
                    continue
                return lang

    # Meson import / tool hints without walking sources
    if "import('python')" in meson_txt or re.search(r"\bpython3?\b", meson_txt):
        if _has_ext_shallow(root, ".py") or "import('python')" in meson_txt:
            return "python"
    if "javac" in meson_txt or re.search(r"\bjava\b", meson_txt):
        if _has_ext_shallow(root, ".java"):
            return "java"

    # --- Shallow source-file checks (src/, cmd/, apps/, tests/, root) ---
    if _has_ext_shallow(root, ".go"):
        return "go"
    if _has_ext_shallow(root, ".rs"):
        return "rust"
    if _has_ext_shallow(root, ".ts"):
        return "typescript"
    if _has_ext_shallow(root, ".cs"):
        return "cs"
    if _has_ext_shallow(root, ".java"):
        return "java"
    if _has_ext_shallow(root, ".py"):
        return "python"
    if _has_ext_shallow(root, ".erl"):
        return "erlang"
    if _has_ext_shallow(root, ".hs"):
        return "haskell"
    if _has_ext_shallow(root, ".st"):
        return "smalltalk"
    if _has_ext_shallow(root, ".swift"):
        return "swift"
    if meson.is_file() and re.search(
        r"project\s*\([^)]*\b(c|cpp)\b", meson_head, re.S
    ):
        if _has_ext_shallow(root, ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"):
            return "c"
    if _has_ext_shallow(root, ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"):
        return "c"

    raise SystemExit(f"could not detect language in {root}")


def append_meson_list_entry(meson_path: Path, list_name: str, entry: str) -> bool:
    """Insert entry into a Meson list like app_sources = [ ... ] if missing."""
    text = meson_path.read_text(encoding="utf-8")
    if entry in text:
        return False
    pattern = re.compile(
        rf"({re.escape(list_name)}\s*=\s*\[)([^\]]*?)(\])",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        return False
    body = match.group(2)
    indent = "    "
    m_indent = re.search(r"\n([ \t]+)'", body)
    if m_indent:
        indent = m_indent.group(1)
    if body.strip():
        new_body = body.rstrip() + "\n" + indent + f"'{entry}',\n"
    else:
        new_body = f"\n{indent}'{entry}',\n"
    text = text[: match.start(2)] + new_body + text[match.end(2) :]
    meson_path.write_text(text, encoding="utf-8")
    return True


def remove_meson_list_entry(meson_path: Path, entry: str) -> bool:
    if not meson_path.is_file():
        return False
    text = meson_path.read_text(encoding="utf-8")
    new, n = re.subn(
        rf"[ \t]*'{re.escape(entry)}',?[ \t]*\n",
        "",
        text,
    )
    if n:
        meson_path.write_text(new, encoding="utf-8")
        return True
    return False


def copy_renamed_file(src: Path, dest: Path, pairs: list[tuple[str, str]]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if is_probably_text(src):
        text = src.read_text(encoding="utf-8")
        dest.write_text(apply_text_replacements(text, pairs), encoding="utf-8")
        mode = src.stat().st_mode
        dest.chmod(mode)
    else:
        shutil.copy2(src, dest)


def relative_to(path: Path, root: Path) -> Path:
    return path.resolve().relative_to(root.resolve())
