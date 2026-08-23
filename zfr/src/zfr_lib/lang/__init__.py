# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-language zephyr template specifications.

Each ``lang/<name>.py`` module exports ``NAME`` and ``SPEC`` (detection weights,
puff paths, meson wiring, lint bits, RPM file lists).

Candidate languages for future templates (not implemented):

- **crystal** — Ruby-like syntax, static typing, native binaries
- **php** — widespread CLI scripts, composer + debian php-* deps
- **dart** — AOT ``dart compile exe`` for standalone CLIs
- **julia** — scientific CLI tools, ``PackageCompiler.jl`` for apps
"""

from __future__ import annotations

import importlib
from pathlib import Path

from ._puff_helpers import puff_generic
from ._score import score_langs as _score_langs
from ._spec import LangSpec
from ._wire import wire_add as _wire_add
from ._wire import wire_remove as _wire_remove

_LANG_ORDER = (
    "antlr",
    "as",
    "bash",
    "bison",
    "c",
    "clib",
    "cobol",
    "cpp",
    "cpplib",
    "csharp",
    "d",
    "erlang",
    "elixir",
    "fortran",
    "gcc",
    "go",
    "haskell",
    "java",
    "kotlin",
    "lua",
    "nim",
    "ocaml",
    "pascal",
    "perl",
    "python",
    "ruby",
    "rust",
    "smalltalk",
    "swift",
    "typescript",
    "zig",
)

CANDIDATE_LANGS = (
    "crystal",
    "php",
    "dart",
    "julia",
)

LANGS = _LANG_ORDER


def _load_specs() -> dict[str, LangSpec]:
    specs: dict[str, LangSpec] = {}
    for name in _LANG_ORDER:
        mod = importlib.import_module(f".{name}", __name__)
        specs[name] = mod.SPEC
    return specs


_SPECS = _load_specs()


def get_spec(lang: str) -> LangSpec:
    try:
        return _SPECS[lang]
    except KeyError as exc:
        raise KeyError(f"unknown language {lang!r}") from exc


def empty_scores() -> dict[str, float]:
    return {lang: 0.0 for lang in LANGS}


def score_langs(root: Path) -> dict[str, float]:
    return _score_langs(root, _SPECS, LANGS)


def rank_langs(root: Path) -> list[tuple[str, float]]:
    scores = score_langs(root)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def detect_lang(workdir: Path | None = None) -> str:
    from .. import _is_zfr_meta_repo, find_project_dir

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


def puff_source_paths(lang: str, tmpl: Path, stem: str, pascal: str) -> list[Path]:
    spec = get_spec(lang)
    if spec.puff_fn is not None:
        return spec.puff_fn(tmpl, stem, pascal)
    return puff_generic(tmpl, stem, pascal)


def wire_add(lang: str, workdir: Path, name: str) -> None:
    _wire_add(get_spec(lang), workdir, name)


def wire_remove(lang: str, workdir: Path, name: str) -> None:
    _wire_remove(get_spec(lang), workdir, name)


def spec_extra_files(lang: str, puffs: list[str]) -> list[str]:
    spec = get_spec(lang)
    if spec.spec_files_fn is None:
        return []
    return spec.spec_files_fn(puffs)


def lint_bits(lang: str, root: Path, role: str) -> list:
    spec = get_spec(lang)
    if spec.lint_fn is None:
        return []
    return spec.lint_fn(root, role)


def skips_shared_example(lang: str) -> bool:
    return get_spec(lang).skip_shared_example
