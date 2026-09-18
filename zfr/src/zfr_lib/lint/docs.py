# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-rule documentation for lint browse (free-form sections)."""

from __future__ import annotations

from dataclasses import dataclass

from ..i18n import _
from ..std import LINT_RULES, StdRule
from .ize_map import ize_command_for_lint, ize_targets_for_lint

Section = tuple[str, str]  # (heading, body)


@dataclass(frozen=True)
class RuleDoc:
    sections: tuple[Section, ...]


def _overrides() -> dict[str, list[Section]]:
    """Explicit per-rule essays. Built at call time so locale switches apply."""
    return {
        "ZL0001": [
            (
                _("Long files fight ownership"),
                _(
                    "Very long source files are hard to review, test, and own. Zephyr "
                    "prefers cohesive modules under a package subdirectory with a thin "
                    "entry-point file — the same shape create/ize expect."
                ),
            ),
            (
                _("What improving it buys you"),
                _(
                    "Smaller review diffs, clearer module boundaries, easier unit "
                    "tests, and fewer merge conflicts on busy files."
                ),
            ),
            (
                _("Thresholds"),
                _(
                    "Lint counts non-empty lines (skipping build/debian/po/…). "
                    "A note appears around ~600 lines; a warning around ~1000. "
                    "Template example modules are skipped."
                ),
            ),
            (
                _("Fixing is manual"),
                _(
                    "Split the file and update meson/install/import lists yourself. "
                    "`zfr ize` does not auto-split sources."
                ),
            ),
        ],
        "ZL0090": [
            (
                _("Hardcoded /usr breaks prefixes"),
                _(
                    "Absolute FHS paths (/usr/share, /usr/bin, …) fail under DESTDIR, "
                    "non-standard prefixes, and Meson configure_file staging."
                ),
            ),
            (
                _("Preferred shape"),
                _(
                    "Scripts use @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (or equivalent) "
                    "and are installed from *.in via Meson."
                ),
            ),
            (
                _("What Solve does"),
                _(
                    "Ize renames affected scripts to *.in and wires configure_file. "
                    "Re-check shebangs and any tests that assumed live paths."
                ),
            ),
        ],
        "ZL0091": [
            (
                _("Version literals drift"),
                _(
                    "A hardcoded release string diverges from debian/changelog and "
                    "Meson project_version() the moment you bump."
                ),
            ),
            (
                _("Single source of truth"),
                _(
                    "Prefer @VERSION@ / PROJECT_VERSION substituted at build time so "
                    "`--version`, wrappers, and packages stay aligned."
                ),
            ),
            (
                _("Risks when converting"),
                _(
                    "C/C++ usually needs config.h; scripts need *.in. Dry-run ize "
                    "(`-n`) on large trees before writing."
                ),
            ),
        ],
        "ZL0094": [
            (
                _("Substitution without a consumer is incomplete"),
                _(
                    "Meson must both define VERSION/PROJECT_VERSION and have sources "
                    "that actually read it — otherwise packaged binaries still lie."
                ),
            ),
            (
                _("How it is checked"),
                _(
                    "Looks for configuration_data keys and for @VERSION@ / "
                    "PROJECT_VERSION usage in installed sources."
                ),
            ),
            (
                _("Closing the loop"),
                _(
                    "Add the missing half (subst or consumer). Solve maps to the "
                    "subst ize steps when available."
                ),
            ),
        ],
        "ZL0095": [
            (
                _("Inline posync is unmaintainable"),
                _(
                    "A bash -euc heredoc inside meson.build duplicates across "
                    "templates and is painful to debug. The contract is "
                    "scripts/posync.sh + run_target('posync')."
                ),
            ),
            (
                _("Payoff"),
                _(
                    "One script to run msgmerge/xgettext locally; ninja posync stays "
                    "short; CI can call the script directly."
                ),
            ),
            (
                _("Solve"),
                _(
                    "Ize extracts the body to scripts/posync.sh and points the "
                    "run_target at it. Verify POTFILES and language flags afterward."
                ),
            ),
        ],
        "ZL0096": [
            (
                _("Maintenance scripts belong under scripts/"),
                _(
                    "look / install-symlinks / deploy helpers at the repo root clutter "
                    "the packaging surface. Zephyr keeps them under scripts/."
                ),
            ),
            (
                _("Detection"),
                _(
                    "Flags root *.sh maintenance names and inline run_target bodies "
                    "that should be externalized."
                ),
            ),
            (
                _("After moving"),
                _(
                    "Update docs and any CI that called the old paths. Solve rewrites "
                    "Meson run_targets to scripts/…"
                ),
            ),
        ],
    }


def _ize_sections(code: str) -> list[Section]:
    targets = ize_targets_for_lint(code)
    cmd = ize_command_for_lint(code)
    if not targets:
        return [
            (
                _("No Solve mapping"),
                _(
                    "This finding has no `zfr ize --only …` shortcut. Follow the "
                    "fix text (or a broader `zfr ize` if several related gaps "
                    "exist), then re-lint."
                ),
            )
        ]
    return [
        (
            _("Solve / ize"),
            _(
                "Clicking Solve runs only: %(targets)s.\n"
                "Equivalent CLI: `%(cmd)s`\n"
                "Use `-n` for a dry plan. Output is captured with fdmux "
                "(ordered stdout/stderr)."
            )
            % {"targets": ", ".join(targets), "cmd": cmd or ""},
        )
    ]


def _category_sections(code: str, rule: StdRule) -> list[Section] | None:
    """Category-flavoured essays with headings that fit the family."""
    title = _(rule.title)
    detail = _(rule.detail) if rule.detail else ""
    sev = rule.default_severity or _("varies")

    if code.startswith("debian."):
        body = detail or (_("Checker `%s` in `zfr lint`.") % rule.code)
        return [
            (
                _("Debian is the APT contract"),
                _(
                    "control / rules / copyright / source format decide how the "
                    "package builds and what users install. Zephyr standardizes on "
                    "Meson + dh `--buildsystem=meson --builddirectory=debian/build`."
                ),
            ),
            (
                _("This check: %s") % title,
                body + "\n" + (_("Default severity hint: %s.") % sev),
            ),
            (
                _("Why it matters"),
                _(
                    "Wrong Architecture, missing Build-Depends, or a non-Meson "
                    "rules file fail debuild or produce unloadable packages even "
                    "when local compiles succeed."
                ),
            ),
            (
                _("When editing packaging"),
                _(
                    "Ize may rewrite from templates — always diff Maintainer, "
                    "Depends, and Architecture before upload."
                ),
            ),
        ]
    if code.startswith("rpm."):
        body = detail or (_("Checker `%s`.") % rule.code)
        return [
            (
                _("RPM must mirror Meson/Debian"),
                _(
                    "spec %files, BuildArch, and Version have to describe the same "
                    "payload Meson installs. Project-local rpmbuild TOPDIR and "
                    "stale file lists are common failure modes."
                ),
            ),
            (
                _("This check: %s") % title,
                body + "\n" + (_("Severity hint: %s.") % sev),
            ),
            (
                _("Typical fallout"),
                _(
                    "Unpackaged files, wrong noarch/ELF, leftover rpmbuild/, or "
                    "Debian substvars copied into Requires."
                ),
            ),
        ]
    if code.startswith("meson."):
        return [
            (
                _("Meson is the build system of record"),
                _(
                    "Identity, license, version source, man pages, completion, "
                    "and look/posync targets live in meson.build. Drift here "
                    "breaks Debian and RPM alike."
                ),
            ),
            (
                _("This check: %s") % title,
                detail
                or (_("Parses meson.build for `%s` expectations.") % rule.code),
            ),
            (
                _("Editing tips"),
                _(
                    "Ize patches meson.build; reconcile custom targets with "
                    "template blocks and re-configure after large edits."
                ),
            ),
        ]
    if code.startswith("i18n."):
        return [
            (
                _("Locales are a product surface"),
                _(
                    "Gettext catalogs and whole-document man/<locale>/ pages gate "
                    "what users see at the configured l10n level (`-l` / "
                    "lint.options)."
                ),
            ),
            (
                _("This check: %s") % title,
                detail
                or _(
                    "Looks at LINGUAS, .po wrap/quality, and man coverage."
                ),
            ),
            (
                _("Human work remains"),
                _(
                    "Ize can stub .po files and fix wrap style; real translation "
                    "and man localization still need people (or `zfr translate`)."
                ),
            ),
        ]
    if code.startswith("layout."):
        return [
            (
                _("Shared layout keeps tools oriented"),
                _(
                    "LICENSE, man/, VERSION, hooks, completion, and scripts/ are "
                    "the landmarks create/ize/lint/release expect."
                ),
            ),
            (
                _("Missing or wrong: %s") % title,
                detail
                or (
                    _("`%s` checks presence/content against the language template.")
                    % rule.code
                ),
            ),
            (
                _("Scaffold refresh"),
                _(
                    "Solve may install or refresh files from the template "
                    "(.githooks, LICENSE, cursor rules, …). Review before commit."
                ),
            ),
        ]
    if code.startswith("lang."):
        return [
            (
                _("Language-template expectations"),
                _(
                    "%(title)s. Each language keeps idiomatic markers "
                    "(tests/, Cargo.toml, bas i18n helpers, bash *.in, …) so the "
                    "tree stays packagable."
                )
                % {"title": title},
            ),
            (
                _("Details"),
                detail
                or (
                    _("Implemented as `%s`; severity hint %s.")
                    % (rule.code, sev)
                ),
            ),
        ]
    if code.startswith("identity."):
        return [
            (
                _("One name across ecosystems"),
                _(
                    "Directory name, meson project(), debian Source, and RPM Name "
                    "must agree. Mismatches confuse rename, release, and repos."
                ),
            ),
            (
                _("Check: %s") % title,
                detail or (_("`%s` compares identity fields.") % rule.code),
            ),
        ]
    if code.startswith("source."):
        return [
            (
                _("Source hygiene"),
                _(
                    "%(title)s. Covers length and hardcoded paths/versions "
                    "that break relocatable installs."
                )
                % {"title": title},
            ),
            (
                _("How lint looks"),
                detail
                or _(
                    "Counts lines and/or scans for FHS paths and version tokens."
                ),
            ),
        ]
    if code.startswith("tokens.") or code.startswith("template.") or code.startswith(
        "readme."
    ):
        return [
            (
                title,
                detail
                or (
                    _(
                        "`%s` keeps templates instantiable and apps free "
                        "of leftover placeholders / banners."
                    )
                    % rule.code
                ),
            ),
        ]
    return None


def _generic_sections(rule: StdRule) -> list[Section]:
    sev = rule.default_severity or _("varies")
    detail = _(rule.detail) if rule.detail else ""
    what = ((detail + "\n\n") if detail else "") + (
        _(
            "Implemented under `%s` in `zfr lint`. Findings carry "
            "a concrete fix string when possible. Remap severity with "
            "`-w` / `-e` / `--strict`."
        )
        % rule.code
    )
    return [
        (
            _(rule.title),
            _(
                "Rule %(id)s (`%(code)s`) is part of the zephyr packaging/"
                "layout contract. Default severity hint: %(sev)s."
            )
            % {"id": rule.id, "code": rule.code, "sev": sev},
        ),
        (
            _("What lint does"),
            what,
        ),
        (
            _("Changing the tree"),
            _(
                "Fixes may touch packaging, meson.build, sources, or scaffold "
                "copies. Diff Maintainer, Depends, %files, and *.in scripts "
                "before upload."
            ),
        ),
    ]


def rule_doc_for(rule_id: str, code: str) -> RuleDoc:
    rule = LINT_RULES.by_id(rule_id) or LINT_RULES.lookup(code)
    if rule is None:
        rule = StdRule(rule_id, code, code)

    ov_map = _overrides()
    ov = ov_map.get(rule.id) or ov_map.get(rule_id)
    if ov:
        sections = list(ov)
    else:
        sections = _category_sections(code, rule) or _generic_sections(rule)

    # Close with Solve/ize note unless the essay already covered it.
    ize = _ize_sections(code)
    already = any(
        "olve" in (t + b).lower() or "ize" in (t + b).lower() for t, b in sections
    )
    if not already:
        sections.extend(ize)

    cleaned: list[Section] = []
    for title, body in sections:
        t = title.strip()
        b = body.strip()
        if t and b:
            cleaned.append((t, b))
    return RuleDoc(sections=tuple(cleaned))


def rule_doc_dict(rule_id: str, code: str) -> dict[str, object]:
    d = rule_doc_for(rule_id, code)
    return {
        "sections": [{"title": t, "body": b} for t, b in d.sections],
    }
