# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared helpers for the zfr CLI tools (zephyr template collection)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Literal

# Placeholder example app name shipped in templates.
TEMPLATE_PUFF = "some_puff1"

# Zephyr style: gettext catalogs should cover at least these locales.
# English (en) is the source msgid language and is not listed in LINGUAS.
# User-facing aliases zh-cn / zh-tw map to gettext zh_CN / zh_TW.
# Default lint level is L1; see zfr_lib.l10n.L10N_LEVELS for L0–L3 tier coverage.
from .l10n import L10N_LEVELS, linguas_for_level, parse_l10n_level

RECOMMENDED_I18N_SOURCE = "en"
RECOMMENDED_I18N_LINGUAS = L10N_LEVELS["L1"]

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".cursor",
    ".vscode",
    "build",
    # debian/ is included so create/rename rewrite Source/Package/Description
    "dist",
    "rpmbuild",
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


def instantiation_pairs(
    project: str, puff: str | None = None
) -> list[tuple[str, str]]:
    """Pairs to instantiate a template: puff tokens first, then project tokens."""
    pairs: list[tuple[str, str]] = []
    if puff:
        pairs.extend(replacement_pairs(TEMPLATE_PUFF, puff))
    if project and project != "zephyr":
        # Template placeholder is still "zephyr"; CLI name "zfr" is never rewritten.
        pairs.extend(replacement_pairs("zephyr", project))
    return pairs


def _relative_skip_parts(path: Path, root: Path) -> bool:
    """Skip only dirs under *root* (not e.g. a parent named bin/ or zephyr/)."""
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return any(part in SKIP_DIR_NAMES for part in rel.parts)


def _looks_like_template_root(path: Path) -> bool:
    """True if *path* holds multiple zephyr language template trees."""
    n = sum(
        1
        for lang in ("c", "clib", "python", "rust")
        if (path / lang / "meson.build").is_file()
    )
    return n >= 2


def pkgdatadir() -> Path:
    env = os.environ.get("ZFR_PKGDATADIR") or os.environ.get("ZEPHYR_PKGDATADIR")
    if env:
        return Path(env)

    try:
        from . import paths_config  # type: ignore

        return Path(paths_config.PKGDATADIR)
    except Exception:
        pass

    here = Path(__file__).resolve()
    # zfr/src/zfr_lib → zfr/; templates live in the parent monorepo.
    zfr_root = here.parents[2] if here.parent.name == "zfr_lib" else here.parents[1]
    parent = zfr_root.parent
    if _looks_like_template_root(parent):
        return parent
    if _looks_like_template_root(zfr_root):
        return zfr_root

    for base in (Path(sys.prefix), Path("/usr"), Path("/usr/local")):
        cand = base / "share" / "zephyr"
        if cand.is_dir():
            return cand

    return zfr_root


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
    if not pairs:
        return 0, 0
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
            if _relative_skip_parts(p, root):
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


def _is_zfr_meta_repo(root: Path) -> bool:
    """True if root is the multi-language zephyr template meta-repo."""
    lang_meson = sum(
        1 for lang in LANGS if (root / lang / "meson.build").is_file()
    )
    if lang_meson < 3:
        return False
    has_zfr = (
        (root / "zfr" / "src" / "zfr").is_file()
        or (root / "zfr" / "meson.build").is_file()
        or (root / "tools" / "zfr").is_file()
        or (root / "src" / "zfr").is_file()
    )
    meson = root / "meson.build"
    if meson.is_file():
        txt = meson.read_text(encoding="utf-8", errors="ignore")
        if "template_langs" in txt:
            return True
        if "foreach lang" in txt and "pkgdatadir" in txt:
            return True
    zfr_meson = root / "zfr" / "meson.build"
    if zfr_meson.is_file():
        ztxt = zfr_meson.read_text(encoding="utf-8", errors="ignore")
        if "template_langs" in ztxt or "install_templates.py" in ztxt:
            return True
    return has_zfr


def _is_zfr_cli_package(root: Path) -> bool:
    """True if *root* is the zfr CLI / zephyr helper package (not a language template)."""
    return (root / "src" / "zfr").is_file() and (root / "src" / "zfr_lib").is_dir()


_DEP_FIELD = re.compile(
    r"^(Build-Depends(?:-Indep|-Arch)?|Depends|Recommends|Suggests):",
    re.I,
)


def _control_depends_text(control_txt: str) -> str:
    """Keep only Depends / Build-Depends field bodies (not Description)."""
    lines: list[str] = []
    taking = False
    for line in control_txt.splitlines():
        if _DEP_FIELD.match(line):
            taking = True
            lines.append(line)
            continue
        if taking:
            if line.startswith((" ", "\t")):
                lines.append(line)
            else:
                taking = False
    return "\n".join(lines)


def _is_clib_project(root: Path, meson_txt: str, control_txt: str = "") -> bool:
    """Distinguish clib (shared/static lib template) from simple c CLI."""
    if re.search(r"\bshared_library\s*\(", meson_txt):
        return True
    if re.search(r"\bpkgconfig\.generate\s*\(", meson_txt) and (
        root / "src" / "lib.c"
    ).is_file():
        return True
    if (root / "src" / "lib.c").is_file() and re.search(
        r"\bbas-c\b|\blibbas-c(?:-dev)?\b", meson_txt + "\n" + control_txt, re.I
    ):
        return True
    if re.search(r"\blibbas-c-dev\b", control_txt, re.I) and _has_ext_shallow(
        root, ".c", ".h"
    ):
        return True
    return False


def _looks_like_bash_shlib(root: Path, control_txt: str = "") -> bool:
    if re.search(r"\bbash-shlib\b", control_txt, re.I):
        return True
    for base in _shallow_source_dirs(root):
        if base == root:
            candidates = [p for p in root.iterdir() if p.is_file()]
        else:
            candidates = list(iter_files(base))
        for path in candidates:
            try:
                head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
            except OSError:
                continue
            if re.search(r"\bimport\s+cliboot\b", head) or re.search(
                r"(?:^|\n)\s*\. shlib(?:-import)?\b|\bshlib-import\b", head
            ):
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



def _is_cpplib_project(root: Path, meson_txt: str, control_txt: str = "") -> bool:
    """Distinguish cpplib (shared/static lib template) from simple cpp CLI."""
    if re.search(r"\bshared_library\s*\(", meson_txt):
        return True
    if re.search(r"\bpkgconfig\.generate\s*\(", meson_txt) and (
        root / "src" / "lib.cpp"
    ).is_file():
        return True
    if (root / "src" / "lib.cpp").is_file() and re.search(
        r"\bbas-cpp\b|\blibbas-cpp(?:-dev)?\b", meson_txt + "\n" + control_txt, re.I
    ):
        return True
    if re.search(r"\blibbas-cpp-dev\b", control_txt, re.I) and _has_ext_shallow(
        root, ".cpp", ".hpp", ".h"
    ):
        return True
    return False


def find_project_dir(start: Path | None = None) -> Path:
    """Resolve the package directory (monorepo-aware).

    Prefer the nearest *packagedir* with zephyr shape over climbing to a
    multi-language *repodir* (meta-repo root). Standalone repos return the
    same path for package and repo.
    """
    from .shape import find_packagedir

    return find_packagedir(start)



def _git_available(root: Path) -> bool:
    return shutil.which("git") is not None and (root / ".git").exists()


def git_describe_version(root: Path) -> str | None:
    if shutil.which("git") is None:
        return None
    proc = subprocess.run(
        ["git", "describe", "--tags", "--always", "--dirty"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    v = proc.stdout.strip()
    return v or None


def changelog_version(root: Path) -> str | None:
    path = root / "debian" / "changelog"
    if not path.is_file():
        return None
    if shutil.which("dpkg-parsechangelog"):
        proc = subprocess.run(
            ["dpkg-parsechangelog", "-l", str(path), "-S", "Version"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            v = proc.stdout.strip()
            if v:
                return v.split(":", 1)[-1]
    first = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    if not first:
        return None
    m = re.match(r"\S+\s+\(([^)]+)\)", first[0])
    if not m:
        return None
    return m.group(1).split(":", 1)[-1]


def version_file_version(root: Path) -> str | None:
    path = root / "VERSION"
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines:
        return None
    v = lines[0].strip()
    return v or None


def apply_version_modifiers(v: str) -> str:
    """Strip a leading v; wrap a non-semver token as 0.0.0-<token>."""
    v = v.strip()
    if v.startswith("v") and len(v) > 1:
        v = v[1:]
    if not v:
        return "0.0.0"
    core = v[: -len("-dirty")] if v.endswith("-dirty") else v
    if "." not in core:
        return f"0.0.0-{v}"
    return v


def rpm_compatible_version(v: str) -> str:
    """RPM Version cannot contain '-'."""
    return v.replace("-", "_")


def project_version(
    root: Path | None = None,
    *,
    source: Literal["git", "changelog"] | None = None,
    rpm: bool = False,
) -> str:
    """Project version: git describe, changelog, VERSION file, then 0.0.0."""
    root = find_project_dir(root)
    git_ok = _git_available(root)
    if source is None:
        source = "git" if git_ok else "changelog"
    v: str | None = None
    if source == "git":
        v = git_describe_version(root)
    else:
        v = changelog_version(root)
    if not v:
        v = version_file_version(root)
    if not v:
        v = "0.0.0"
    v = apply_version_modifiers(v)
    if rpm:
        v = rpm_compatible_version(v)
    return v


def cli_root() -> Path:
    """Install prefix of this zfr tree (source: zfr/, installed: share/zephyr/zfr)."""
    libdir = Path(__file__).resolve().parent
    parent = libdir.parent
    if parent.name == "src":
        return parent.parent
    return parent


def cli_version(*, rpm: bool = False) -> str:
    """Version of the zfr CLI itself (not the project in cwd)."""
    root = cli_root()
    v = git_describe_version(root)
    if not v:
        v = changelog_version(root)
    if not v:
        v = changelog_version(root.parent)
    if not v:
        v = version_file_version(root)
    if not v:
        v = "0.0.0"
    v = apply_version_modifiers(v)
    if rpm:
        v = rpm_compatible_version(v)
    return v


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


from .lang import CANDIDATE_LANGS, LANGS, detect_lang, empty_scores, rank_langs, score_langs
