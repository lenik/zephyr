# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered zephyr ize rules (ZI001+)."""

from __future__ import annotations

from .registry import RuleRegistry, StdRule

_IZE_RULES: tuple[StdRule, ...] = (
    StdRule("ZI001", "ize.mesonize", "Convert Autotools/CMake with 2meson"),
    StdRule("ZI002", "ize.scaffold", "Add missing language-template scaffold files"),
    StdRule("ZI003", "ize.debian.control", "Patch debian/control for zephyr style"),
    StdRule("ZI004", "ize.debian.rules", "Align debian/rules with Meson dh helper"),
    StdRule("ZI005", "ize.debian.docs", "Sync debian/docs with installed mans"),
    StdRule("ZI006", "ize.changelog", "Ensure debian/changelog and VERSION file"),
    StdRule("ZI007", "ize.hooks", "Install .githooks/pre-commit VERSION sync hook"),
    StdRule("ZI008", "ize.meson.patch", "Patch meson.build (version, license, docs, completion)"),
    StdRule("ZI009", "ize.man.convert", "Convert groff man pages to docs/*.adoc"),
    StdRule("ZI010", "ize.man.stub", "Create AsciiDoc man page stubs"),
    StdRule("ZI011", "ize.meson.man", "Add Meson asciidoctor man page targets"),
    StdRule("ZI012", "ize.completion", "Add bash-completion stubs for command puffs"),
    StdRule("ZI013", "ize.rpm", "Align rpm/Makefile and RPM spec with debian/Meson"),
    StdRule("ZI014", "ize.subst", "Replace hardcoded versions with @VERSION@ / config.h"),
    StdRule("ZI015", "ize.i18n.derive", "Derive child locale gettext catalogs"),
    StdRule("ZI016", "ize.commit", "Bump patch version and git commit (--commit)"),
)

IZE_RULES = RuleRegistry(_IZE_RULES)


def ize_rule_id(code: str) -> str:
    return IZE_RULES.rule_id(code)
