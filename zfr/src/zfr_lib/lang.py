# SPDX-License-Identifier: AGPL-3.0-or-later
"""Language detection via a built-in per-language confidence vector.

Each scanned project file (and a few well-known manifests) adds weight to
one or more language slots. The language with the highest confidence wins.
Debian *Description* text is never consulted — only Depends/Build-Depends.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import (
    LANGS,
    SKIP_DIR_NAMES,
    _is_zfr_meta_repo,
    find_project_dir,
    is_probably_text,
    iter_files,
)

# Extra dirs to skip while scoring (on top of SKIP_DIR_NAMES).
_SCORE_SKIP_DIRS = SKIP_DIR_NAMES | {
    "po",
    "locale",
    ".githooks",
    "githooks",
    "debian",  # debian/control is handled as a special file
}

_SKIP_SUFFIXES = {
    ".md",
    ".markdown",
    ".rst",
    ".adoc",
    ".txt",
    ".po",
    ".pot",
    ".mo",
    ".html",
    ".xml",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".a",
    ".so",
    ".whl",
    ".zip",
    ".gz",
    ".xz",
    ".bz2",
}

_SKIP_NAMES = {
    "license",
    "copying",
    "changelog",
    "authors",
    "news",
    "todo",
    "meson.build",
    "meson_options.txt",
}

_EXT_WEIGHTS: dict[str, dict[str, float]] = {
    ".py": {"python": 3.0},
    ".pyi": {"python": 1.5},
    ".go": {"go": 4.0},
    ".rs": {"rust": 4.0},
    ".ts": {"typescript": 4.0},
    ".tsx": {"typescript": 4.0},
    ".cts": {"typescript": 3.0},
    ".mts": {"typescript": 3.0},
    ".js": {"typescript": 0.35},
    ".mjs": {"typescript": 0.35},
    ".cjs": {"typescript": 0.35},
    ".cs": {"csharp": 4.0},
    ".java": {"java": 4.0},
    ".erl": {"erlang": 4.0},
    ".hrl": {"erlang": 2.0},
    ".hs": {"haskell": 4.0},
    ".lhs": {"haskell": 3.0},
    ".st": {"smalltalk": 4.0},
    ".swift": {"swift": 4.0},
    ".pl": {"perl": 4.0},
    ".pm": {"perl": 3.5},
    ".t": {"perl": 2.0},
    ".rb": {"ruby": 4.0},
    ".sh": {"bash": 1.2},
    ".bash": {"bash": 3.0},
    ".c": {"c": 2.0, "clib": 2.0},
    ".h": {"c": 0.45, "clib": 0.45, "cpp": 0.35, "cpplib": 0.35},
    ".cpp": {"cpp": 3.0, "cpplib": 3.0},
    ".cc": {"cpp": 3.0, "cpplib": 3.0},
    ".cxx": {"cpp": 3.0, "cpplib": 3.0},
    ".hpp": {"cpp": 2.0, "cpplib": 2.0},
    ".hh": {"cpp": 2.0, "cpplib": 2.0},
    ".hxx": {"cpp": 2.0, "cpplib": 2.0},
}

_NAME_WEIGHTS: dict[str, dict[str, float]] = {
    "go.mod": {"go": 30.0},
    "go.sum": {"go": 8.0},
    "cargo.toml": {"rust": 30.0},
    "cargo.lock": {"rust": 8.0},
    "package.json": {"typescript": 10.0},
    "tsconfig.json": {"typescript": 25.0},
    "pnpm-lock.yaml": {"typescript": 5.0},
    "package-lock.json": {"typescript": 5.0},
    "yarn.lock": {"typescript": 5.0},
    "gemfile": {"ruby": 20.0},
    "rakefile": {"ruby": 8.0},
    "makefile.pl": {"perl": 12.0},
    "cpanfile": {"perl": 12.0},
    "mix.exs": {"erlang": 8.0},
    "rebar.config": {"erlang": 20.0},
    "stack.yaml": {"haskell": 20.0},
    "cabal.project": {"haskell": 15.0},
    "package.swift": {"swift": 25.0},
    "pom.xml": {"java": 18.0},
    "build.gradle": {"java": 12.0},
    "build.gradle.kts": {"java": 8.0},
}

_SHEBANG: list[tuple[re.Pattern[str], dict[str, float]]] = [
    (re.compile(r"^#!.*\bpython(?:3(?:\.\d+)?)?\b"), {"python": 4.0}),
    (re.compile(r"^#!.*\b(bash|sh)\b"), {"bash": 3.0}),
    (re.compile(r"^#!.*\bperl\b"), {"perl": 4.0}),
    (re.compile(r"^#!.*\bruby\b"), {"ruby": 4.0}),
    (re.compile(r"^#!.*\bnode\b"), {"typescript": 1.5}),
]

_DEP_FIELD = re.compile(
    r"^(Build-Depends(?:-Indep|-Arch)?|Depends|Recommends|Suggests):",
    re.I,
)

_DEPENDS_WEIGHTS: list[tuple[re.Pattern[str], dict[str, float]]] = [
    (re.compile(r"\bgolang(?:-go)?\b", re.I), {"go": 12.0}),
    (re.compile(r"\b(cargo|rustc)\b", re.I), {"rust": 12.0}),
    (re.compile(r"\b(nodejs|npm|node-typescript|typescript)\b", re.I), {"typescript": 10.0}),
    (re.compile(r"\bdotnet(?:-sdk)?\b", re.I), {"csharp": 12.0}),
    (re.compile(r"\b(default-jdk|default-jre|openjdk|java-runtime)\b", re.I), {"java": 12.0}),
    (re.compile(r"\bpython3(?:-dev)?\b", re.I), {"python": 10.0}),
    (re.compile(r"\berlang\b", re.I), {"erlang": 12.0}),
    (re.compile(r"\b(ghc|haskell-devscripts)\b", re.I), {"haskell": 12.0}),
    (re.compile(r"\bgnu-smalltalk\b", re.I), {"smalltalk": 12.0}),
    (re.compile(r"\bswift(?:lang)?\b", re.I), {"swift": 12.0}),
    (re.compile(r"\bbash-shlib\b", re.I), {"bash": 18.0}),
    (re.compile(r"\bperl\b", re.I), {"perl": 8.0}),
    (re.compile(r"\bruby\b", re.I), {"ruby": 8.0}),
    (re.compile(r"\blibbas-cpp-dev\b", re.I), {"cpplib": 16.0}),
    (re.compile(r"\blibbas-c-dev\b", re.I), {"clib": 16.0}),
]


def empty_scores() -> dict[str, float]:
    return {lang: 0.0 for lang in LANGS}


def _add(scores: dict[str, float], weights: dict[str, float], factor: float = 1.0) -> None:
    for lang, w in weights.items():
        if lang in scores:
            scores[lang] += w * factor


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
    if re.search(r"\bshared_library\s*\(", meson_txt):
        return True
    if re.search(r"\bpkgconfig\.generate\s*\(", meson_txt) and (root / "src" / "lib.c").is_file():
        return True
    if (root / "src" / "lib.c").is_file() and re.search(
        r"\bbas-c\b|\blibbas-c(?:-dev)?\b", meson_txt + "\n" + control_txt, re.I
    ):
        return True
    return False


def _is_cpplib_project(root: Path, meson_txt: str, control_txt: str = "") -> bool:
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
    return False


def _looks_like_bash_shlib(root: Path, control_txt: str = "") -> bool:
    if re.search(r"\bbash-shlib\b", control_txt, re.I):
        return True
    src = root / "src"
    bases = [root]
    if src.is_dir():
        bases.append(src)
    for base in bases:
        try:
            paths = [p for p in base.iterdir() if p.is_file()] if base == root else list(iter_files(base))
        except OSError:
            continue
        for path in paths:
            try:
                head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
            except OSError:
                continue
            if re.search(r"\bimport\s+cliboot\b", head) or re.search(
                r"(?:^|\n)\s*\. shlib(?:-import)?\b|\bshlib-import\b", head
            ):
                return True
    return False


def _should_skip_file(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    parts = {p.lower() for p in rel.parts[:-1]}
    if parts & {n.lower() for n in _SCORE_SKIP_DIRS}:
        return True
    if path.suffix.lower() in _SKIP_SUFFIXES:
        return True
    if path.name.lower() in _SKIP_NAMES:
        return True
    return False


def _score_meson(scores: dict[str, float], text: str) -> None:
    head = text[:2500]
    m = re.search(r"project\s*\((.*?)\)", head, re.S)
    if m:
        tokens = [x.lower() for x in re.findall(r"['\"]([A-Za-z+#]+)['\"]", m.group(1))]
        for tok in tokens[1:]:
            if tok == "c":
                _add(scores, {"c": 18.0, "clib": 18.0})
            elif tok in ("cpp", "c++"):
                _add(scores, {"cpp": 18.0, "cpplib": 18.0})
            elif tok == "rust":
                _add(scores, {"rust": 20.0})
            elif tok in LANGS:
                _add(scores, {tok: 18.0})
    if "import('python')" in text or 'import("python")' in text:
        _add(scores, {"python": 16.0})
    if re.search(r"\bjavac\b|\bjava\b", text) and ".java" in text:
        _add(scores, {"java": 8.0})


def _score_depends(scores: dict[str, float], depends: str) -> None:
    if not depends:
        return
    for pat, weights in _DEPENDS_WEIGHTS:
        if pat.search(depends):
            _add(scores, weights)


def _score_file(scores: dict[str, float], path: Path) -> None:
    name = path.name.lower()
    if name in _NAME_WEIGHTS:
        _add(scores, _NAME_WEIGHTS[name])
    suffix = path.suffix.lower()
    if suffix in _EXT_WEIGHTS:
        _add(scores, _EXT_WEIGHTS[suffix])
    if suffix in {".csproj", ".sln"} or name.endswith(".csproj"):
        _add(scores, {"csharp": 18.0})
    if name.endswith(".cabal"):
        _add(scores, {"haskell": 18.0})
    if not is_probably_text(path):
        return
    try:
        head = path.read_bytes()[:256].decode("utf-8", errors="ignore")
    except OSError:
        return
    first = head.splitlines()[:2]
    blob = "\n".join(first)
    for pat, weights in _SHEBANG:
        if pat.search(blob):
            _add(scores, weights)
            break


def score_langs(root: Path) -> dict[str, float]:
    """Return a confidence vector over LANGS for *root*."""
    scores = empty_scores()
    meson = root / "meson.build"
    meson_txt = meson.read_text(encoding="utf-8", errors="ignore") if meson.is_file() else ""
    if meson_txt:
        _score_meson(scores, meson_txt)

    control = root / "debian" / "control"
    control_txt = (
        control.read_text(encoding="utf-8", errors="ignore") if control.is_file() else ""
    )
    depends = _control_depends_text(control_txt)
    _score_depends(scores, depends)

    for path in iter_files(root):
        if _should_skip_file(path, root):
            continue
        # debian/control is scored via Depends only (above).
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if rel.parts[:1] == ("debian",) and path.name.lower() == "control":
            continue
        if path.name.lower() == "meson.build" and path.parent == root:
            continue
        _score_file(scores, path)

    if _looks_like_bash_shlib(root, depends):
        _add(scores, {"bash": 14.0})

    if _is_clib_project(root, meson_txt, depends):
        scores["clib"] += 22.0
        scores["c"] *= 0.2
    else:
        scores["c"] += 4.0 if scores["c"] else 0.0
        scores["clib"] *= 0.2

    if _is_cpplib_project(root, meson_txt, depends):
        scores["cpplib"] += 22.0
        scores["cpp"] *= 0.2
    else:
        scores["cpp"] += 4.0 if scores["cpp"] else 0.0
        scores["cpplib"] *= 0.2

    return scores


def rank_langs(root: Path) -> list[tuple[str, float]]:
    scores = score_langs(root)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def detect_lang(workdir: Path | None = None) -> str:
    """Detect zephyr template language: max confidence in the langs vector."""
    root = find_project_dir(workdir)
    if _is_zfr_meta_repo(root):
        raise SystemExit(
            f"{root} looks like the zephyr meta-repo root "
            "(multiple language templates). "
            "Run zfr from a language project directory "
            "(e.g. clib/, cpp/, cpplib/, c/, bash/, perl/, ruby/, python/, rust/), "
            "not the repository root."
        )
    ranked = rank_langs(root)
    if not ranked or ranked[0][1] <= 0:
        raise SystemExit(f"could not detect language in {root}")
    return ranked[0][0]
