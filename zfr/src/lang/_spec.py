# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-language specification objects."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from re import Pattern
from typing import Any

PuffFn = Callable[[Path, str, str], list[Path]]
LintFn = Callable[[Path, str], list[Any]]
ScoreFn = Callable[[Path, dict[str, float], str, str], None]
SpecFilesFn = Callable[[list[str]], list[str]]


@dataclass(frozen=True)
class WireSpec:
    """How ``zfr add`` / ``zfr remove`` patch meson.build for a puff."""

    kind: str = "none"  # c, script, python, csharp, go, none
    app_list: str = "app_sources"
    bash_list: str = "bash_files"
    app_ext: str = ""
    script_ext: str = ""
    test_ext: str = ""
    man: bool = True


@dataclass(frozen=True)
class LangSpec:
    name: str
    ext_weights: dict[str, float] = field(default_factory=dict)
    name_weights: dict[str, float] = field(default_factory=dict)
    shebangs: tuple[tuple[Pattern[str], float], ...] = ()
    depends: tuple[tuple[Pattern[str], float], ...] = ()
    meson_tokens: dict[str, float] = field(default_factory=dict)
    meson_hints: tuple[tuple[str, float], ...] = ()
    wire: WireSpec = field(default_factory=WireSpec)
    puff_fn: PuffFn | None = None
    lint_fn: LintFn | None = None
    spec_files_fn: SpecFilesFn | None = None
    score_fn: ScoreFn | None = None
    skip_shared_example: bool = False
