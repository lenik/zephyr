# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered zephyr ize rules (ZI0001+)."""

from __future__ import annotations

from .registry import RuleRegistry, StdRule

_IZE_RULES: tuple[StdRule, ...] = (
    StdRule("ZI0001", "ize.mesonize", "Convert Autotools/CMake with 2meson"),
    StdRule("ZI0002", "ize.scaffold", "Add missing language-template scaffold files"),
    StdRule("ZI0003", "ize.debian.control", "Patch debian/control for zephyr style"),
    StdRule("ZI0004", "ize.debian.rules", "Align debian/rules with Meson dh helper"),
    StdRule("ZI0005", "ize.debian.docs", "Sync debian/docs with installed mans"),
    StdRule("ZI0006", "ize.changelog", "Ensure debian/changelog and VERSION file"),
    StdRule("ZI0007", "ize.stdfiles", "Refresh LICENSE, .githooks, .cursor/rules from shipped zfr copies"),
    StdRule("ZI0008", "ize.meson.patch", "Patch meson.build (version, license, docs, completion)"),
    StdRule("ZI0009", "ize.man.convert", "Convert groff man pages to man/*.adoc"),
    StdRule("ZI0010", "ize.man.stub", "Create AsciiDoc man page stubs"),
    StdRule("ZI0011", "ize.meson.man", "Add Meson asciidoctor man page targets"),
    StdRule("ZI0012", "ize.completion", "Add bash-completion stubs for command puffs"),
    StdRule("ZI0013", "ize.rpm", "Align packaging/rpm/Makefile and RPM spec with debian/Meson"),
    StdRule("ZI0014", "ize.subst", "Replace hardcoded versions/paths with @VERSION@/@PREFIX@ / config.h"),
    StdRule("ZI0015", "ize.i18n.derive", "Meson build+install derived locale catalogs"),
    StdRule("ZI0016", "ize.i18n.po-nowrap", "Rewrite source .po catalogs without line wrapping"),
    StdRule("ZI0017", "ize.commit", "Bump patch version and git commit (--commit)"),
    StdRule("ZI0018", "ize.i18n.coverage", "Ensure LINGUAS + .po for lint l10n level"),
    StdRule(
        "ZI0019",
        "ize.i18n.man-locale",
        "Do not scaffold man/<locale>/*.adoc (missing man translations are lint-only)",
    ),
    StdRule("ZI0020", "ize.rpm.leftover", "Remove project-local rpmbuild/ leftover tree"),
    StdRule(
        "ZI0021",
        "ize.c.bas",
        "C-family bas i18n/logger/LOCALEDIR and gettext spacing",
    ),
    StdRule(
        "ZI0022",
        "ize.posync",
        "Externalize posync run_target to scripts/posync.sh",
    ),
    StdRule(
        "ZI0023",
        "ize.scripts",
        "Move build/deploy/maintenance scripts under scripts/",
    ),
)

IZE_RULES = RuleRegistry(_IZE_RULES)


def ize_rule_id(code: str) -> str:
    return IZE_RULES.rule_id(code)
