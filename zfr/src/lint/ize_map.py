# SPDX-License-Identifier: AGPL-3.0-or-later
"""Map lint finding codes to ``zfr ize --only`` targets."""

from __future__ import annotations

from std import LINT_RULES


def ize_targets_for_lint(code: str) -> list[str]:
    """Return ize rule codes to run for a lint finding (empty if not izeable)."""
    rule = LINT_RULES.lookup(code)
    if rule is None or not rule.izeable:
        return []

    if code.startswith("layout.posync") or code == "layout.posync":
        return ["ize.posync"]
    if code.startswith("layout.scripts") or code == "layout.scripts":
        return ["ize.scripts"]
    if code.startswith("layout.man"):
        return ["ize.man.convert", "ize.man.stub", "ize.meson.man"]
    if code.startswith("layout.completion"):
        return ["ize.completion"]
    if code.startswith("layout.VERSION") or code.startswith("layout.pre-commit"):
        return ["ize.changelog", "ize.stdfiles"]
    if code.startswith("layout."):
        return ["ize.scaffold", "ize.stdfiles", "ize.changelog", "ize.completion"]

    if code.startswith("debian.rules"):
        return ["ize.debian.rules"]
    if code.startswith("debian.") or code.startswith("debian"):
        return ["ize.debian.control", "ize.debian.rules", "ize.debian.docs", "ize.changelog"]

    if code.startswith("meson.foreach_puff") or code.startswith("meson.version"):
        return ["ize.meson.patch", "ize.subst"]
    if code.startswith("meson.asciidoctor") or code.startswith("meson.look"):
        return ["ize.meson.man", "ize.meson.patch"]
    if code.startswith("meson."):
        return ["ize.meson.patch", "ize.meson.man", "ize.completion"]

    if code.startswith("rpm.topdir.leftover"):
        return ["ize.rpm.leftover"]
    if code.startswith("rpm."):
        return ["ize.rpm", "ize.rpm.leftover"]

    if code.startswith("source.hardcoded") or code == "meson.version_subst":
        return ["ize.subst"]

    if code.startswith("i18n.po.wrap"):
        return ["ize.i18n.po-nowrap"]
    if code.startswith("i18n."):
        return ["ize.i18n.coverage", "ize.i18n.derive", "ize.i18n.po-nowrap"]

    if code.startswith("lang.c.bas"):
        return ["ize.c.bas"]

    if code.startswith("template."):
        return ["ize.scaffold"]

    if code.startswith("identity.rpm"):
        return ["ize.rpm"]

    if code.startswith("ci."):
        return ["ize.stdfiles"]

    return []


def ize_command_for_lint(code: str, *, dry_run: bool = False) -> str | None:
    """Shell-ish command line for the browse UI (None if not izeable)."""
    targets = ize_targets_for_lint(code)
    if not targets:
        return None
    parts = ["zfr", "ize"]
    if dry_run:
        parts.append("-n")
    for t in targets:
        parts.extend(["--only", t])
    return " ".join(parts)
