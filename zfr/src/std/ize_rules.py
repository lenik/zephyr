# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered zephyr ize rules (ZI0001+)."""

from __future__ import annotations

from i18n import N_

from .registry import RuleRegistry, StdRule

_IZE_RULES: tuple[StdRule, ...] = (
    StdRule("ZI0001", "ize.mesonize", N_("Convert Autotools/CMake with 2meson")),
    StdRule("ZI0002", "ize.scaffold", N_("Add missing language-template scaffold files")),
    StdRule("ZI0003", "ize.debian.control", N_("Patch debian/control for zephyr style")),
    StdRule("ZI0004", "ize.debian.rules", N_("Align debian/rules with Meson dh helper")),
    StdRule("ZI0005", "ize.debian.docs", N_("Sync debian/docs with installed mans")),
    StdRule("ZI0006", "ize.changelog", N_("Ensure debian/changelog and VERSION file")),
    StdRule("ZI0007", "ize.stdfiles", N_("Refresh LICENSE, .githooks, .cursor/rules from shipped zfr copies")),
    StdRule("ZI0008", "ize.meson.patch", N_("Patch meson.build (version, license, docs, completion)")),
    StdRule("ZI0009", "ize.man.convert", N_("Convert groff man pages to man/*.adoc")),
    StdRule("ZI0010", "ize.man.stub", N_("Create AsciiDoc man page stubs")),
    StdRule("ZI0011", "ize.meson.man", N_("Add Meson asciidoctor man page targets")),
    StdRule("ZI0012", "ize.completion", N_("Add bash-completion stubs for command puffs")),
    StdRule("ZI0013", "ize.rpm", N_("Align packaging/rpm/Makefile and RPM spec with debian/Meson")),
    StdRule("ZI0014", "ize.subst", N_("Replace hardcoded versions/paths with @VERSION@/@PREFIX@ / config.h")),
    StdRule("ZI0015", "ize.i18n.derive", N_("Meson build+install derived locale catalogs")),
    StdRule("ZI0016", "ize.i18n.po-nowrap", N_("Rewrite source .po catalogs without line wrapping")),
    StdRule("ZI0017", "ize.commit", N_("Bump patch version and git commit (--commit)")),
    StdRule("ZI0018", "ize.i18n.coverage", N_("Ensure LINGUAS + .po for lint l10n level")),
    StdRule(
        "ZI0019",
        "ize.i18n.man-locale",
        N_("Do not scaffold man/<locale>/*.adoc (missing man translations are lint-only)"),
    ),
    StdRule("ZI0020", "ize.rpm.leftover", N_("Remove project-local rpmbuild/ leftover tree")),
    StdRule(
        "ZI0021",
        "ize.c.bas",
        N_("C-family bas i18n/logger/LOCALEDIR and gettext spacing"),
    ),
    StdRule(
        "ZI0022",
        "ize.posync",
        N_("Externalize posync run_target to scripts/posync.sh"),
    ),
    StdRule(
        "ZI0023",
        "ize.scripts",
        N_("Move build/deploy/maintenance scripts under scripts/"),
    ),
)

IZE_RULES = RuleRegistry(_IZE_RULES)


def ize_rule_id(code: str) -> str:
    return IZE_RULES.rule_id(code)
