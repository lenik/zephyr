# SPDX-License-Identifier: AGPL-3.0-or-later
"""Language detection scoring (confidence vector over LANGS)."""

from __future__ import annotations

import re
from pathlib import Path

from .. import SKIP_DIR_NAMES, is_probably_text, iter_files
from ._spec import LangSpec

_SCORE_SKIP_DIRS = SKIP_DIR_NAMES | {
    "po",
    "locale",
    ".githooks",
    "githooks",
    "debian",
}

_SKIP_SUFFIXES = {
    ".md", ".markdown", ".rst", ".adoc", ".txt", ".po", ".pot", ".mo",
    ".html", ".xml", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".ico", ".pdf", ".pyc", ".pyo", ".class", ".o", ".a", ".so", ".whl",
    ".zip", ".gz", ".xz", ".bz2",
}

_SKIP_NAMES = {
    "license", "copying", "changelog", "authors", "news", "todo",
    "meson.build", "meson_options.txt",
}

_DEP_FIELD = re.compile(
    r"^(Build-Depends(?:-Indep|-Arch)?|Depends|Recommends|Suggests):",
    re.I,
)


def empty_scores(langs: tuple[str, ...]) -> dict[str, float]:
    return {lang: 0.0 for lang in langs}


def _add(scores: dict[str, float], weights: dict[str, float], factor: float = 1.0) -> None:
    for lang, w in weights.items():
        if lang in scores:
            scores[lang] += w * factor


def control_depends_text(control_txt: str) -> str:
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


def score_meson(scores: dict[str, float], specs: dict[str, LangSpec], text: str) -> None:
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
            elif tok in specs:
                spec = specs[tok]
                if spec.meson_tokens:
                    _add(scores, spec.meson_tokens)
                else:
                    _add(scores, {tok: 18.0})
    for spec in specs.values():
        for hint, weight in spec.meson_hints:
            if hint in text:
                _add(scores, {spec.name: weight})


def score_depends(scores: dict[str, float], specs: dict[str, LangSpec], depends: str) -> None:
    if not depends:
        return
    for spec in specs.values():
        for pat, weight in spec.depends:
            if pat.search(depends):
                _add(scores, {spec.name: weight})


def score_file(scores: dict[str, float], specs: dict[str, LangSpec], path: Path) -> None:
    name = path.name.lower()
    for spec in specs.values():
        if name in spec.name_weights:
            _add(scores, {spec.name: spec.name_weights[name]})
    suffix = path.suffix.lower()
    ext_hits: dict[str, float] = {}
    for spec in specs.values():
        if suffix in spec.ext_weights:
            ext_hits[spec.name] = ext_hits.get(spec.name, 0.0) + spec.ext_weights[suffix]
    _add(scores, ext_hits)
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
    blob = "\n".join(head.splitlines()[:2])
    for spec in specs.values():
        for pat, weight in spec.shebangs:
            if pat.search(blob):
                _add(scores, {spec.name: weight})
                return


def score_langs(root: Path, specs: dict[str, LangSpec], langs: tuple[str, ...]) -> dict[str, float]:
    scores = empty_scores(langs)
    meson = root / "meson.build"
    meson_txt = meson.read_text(encoding="utf-8", errors="ignore") if meson.is_file() else ""
    if meson_txt:
        score_meson(scores, specs, meson_txt)

    control = root / "debian" / "control"
    control_txt = control.read_text(encoding="utf-8", errors="ignore") if control.is_file() else ""
    depends = control_depends_text(control_txt)
    score_depends(scores, specs, depends)

    for path in iter_files(root):
        if _should_skip_file(path, root):
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if rel.parts[:1] == ("debian",) and path.name.lower() == "control":
            continue
        if path.name.lower() == "meson.build" and path.parent == root:
            continue
        score_file(scores, specs, path)

    for spec in specs.values():
        if spec.score_fn is not None:
            spec.score_fn(root, scores, meson_txt, depends)

    return scores
