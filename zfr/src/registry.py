# SPDX-License-Identifier: AGPL-3.0-or-later
"""Registered zfr subcommands (lazy-loaded one module per command)."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from dataclasses import dataclass
from types import ModuleType


@dataclass(frozen=True)
class CommandSpec:
    """Lightweight command metadata (no module import until needed)."""

    name: str
    help: str  # gettext msgid
    module: str


# Help strings are English msgids (same as each module's HELP = _("…")).
COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec("create", "create a new project from a language template", "create"),
    CommandSpec("rename", "rename zephyr project and example puff names", "rename"),
    CommandSpec("add", "instantiate puff(s) from the language template", "add"),
    CommandSpec("remove", "remove puff(s) from the current project", "remove"),
    CommandSpec(
        "about",
        "print current project information (walks parents from cwd)",
        "about",
    ),
    CommandSpec(
        "version",
        "print current project version (walks parents from cwd)",
        "version",
    ),
    CommandSpec(
        "lint",
        "validate project packaging and zephyr layout (walks parents from cwd)",
        "lint",
    ),
    CommandSpec(
        "lintsel",
        "interactively select lint rules to ignore or force",
        "lintsel",
    ),
    CommandSpec(
        "izesel",
        "interactively select ize rules to ignore or force",
        "izesel",
    ),
    CommandSpec(
        "comments",
        "print project/user lint.comments with an AI work hint",
        "comments_cmd",
    ),
    CommandSpec(
        "shape",
        "print zephyr package shape score 0-100 (packagedir vs repodir in monorepos)",
        "shape",
    ),
    CommandSpec(
        "dist",
        "build a source tarball (meson dist, or this project only)",
        "dist",
    ),
    CommandSpec(
        "build",
        "detect build system and compile the project",
        "build",
    ),
    CommandSpec(
        "package",
        "detect packaging type and build packages",
        "package",
    ),
    CommandSpec(
        "lasterror",
        "browse the last zfr package output interactively",
        "lasterror",
    ),
    CommandSpec(
        "release",
        "tag, build, package, install, and upload (private cloud)",
        "release",
    ),
    CommandSpec(
        "publish",
        "release then publish to marketplaces (npm / VSIX)",
        "publish",
    ),
    CommandSpec("ize", "refactor this project to current zephyr style", "ize"),
    CommandSpec("i18n", "manage implemented gettext locales", "i18n.cmd"),
    CommandSpec(
        "translate",
        "query and update gettext message strings",
        "translate",
    ),
    CommandSpec(
        "detect",
        "print detected language for the current directory",
        "detect",
    ),
)

_BY_NAME = {spec.name: spec for spec in COMMAND_SPECS}
_LOADED: dict[str, ModuleType] = {}


def command_names() -> list[str]:
    return [spec.name for spec in COMMAND_SPECS]


def get_spec(name: str) -> CommandSpec | None:
    return _BY_NAME.get(name)


def load_command(name: str) -> ModuleType:
    """Import and cache the command module for *name*."""
    if name in _LOADED:
        return _LOADED[name]
    spec = _BY_NAME.get(name)
    if spec is None:
        raise KeyError(name)
    mod = importlib.import_module(spec.module)
    _LOADED[name] = mod
    return mod


def load_all_commands() -> Sequence[ModuleType]:
    """Import every command module (tests / full parser registration)."""
    return tuple(load_command(spec.name) for spec in COMMAND_SPECS)


# Back-compat: some tests may still iterate COMMANDS. Prefer load_command.
class _CommandsProxy(Sequence[ModuleType]):
    def __len__(self) -> int:
        return len(COMMAND_SPECS)

    def __getitem__(self, index):  # type: ignore[no-untyped-def]
        if isinstance(index, slice):
            names = [spec.name for spec in COMMAND_SPECS[index]]
            return [load_command(n) for n in names]
        return load_command(COMMAND_SPECS[index].name)

    def __iter__(self):
        for spec in COMMAND_SPECS:
            yield load_command(spec.name)


COMMANDS: Sequence[ModuleType] = _CommandsProxy()
