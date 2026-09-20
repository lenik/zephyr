# SPDX-License-Identifier: AGPL-3.0-or-later
"""Numbered zephyr lint rules (ZL0001+)."""

from __future__ import annotations

from i18n import N_

from .registry import RuleRegistry, StdRule

# izeable=True → `zfr ize` is documented as a resolution (Fix column on -L).
_LINT_RULES: tuple[StdRule, ...] = (
    StdRule("ZL0001", "source.long", N_("Source file length; extract to package subdirectory"), "varies"),
    StdRule("ZL0002", "source.size", N_("No oversized source files"), "ok"),
    StdRule("ZL0003", "layout.*", N_("Required layout file present or missing"), "varies", izeable=True),
    StdRule("ZL0004", "layout.man", N_("AsciiDoc man page sources under man/"), "varies", izeable=True),
    StdRule("ZL0005", "layout.completion", N_("Bash completion script at project root"), "varies", izeable=True),
    StdRule("ZL0006", "layout.VERSION", N_("VERSION file synced with changelog"), "varies", izeable=True),
    StdRule("ZL0007", "layout.pre-commit", N_("Git pre-commit hook syncs VERSION"), "varies", izeable=True),
    StdRule("ZL0008", "debian.build-depends.*", N_("debian/control Build-Depends entry"), "varies", izeable=True),
    StdRule("ZL0009", "debian.debhelper", N_("debhelper-compat in Build-Depends"), "varies", izeable=True),
    StdRule("ZL0010", "debian.Architecture", N_("debian/control Architecture field"), "varies", izeable=True),
    StdRule("ZL0011", "debian.Architecture.elf", N_("ELF binary vs Architecture: all"), "error"),
    StdRule("ZL0012", "debian.Homepage", N_("debian/control Homepage field"), "varies", izeable=True),
    StdRule("ZL0013", "debian.rules", N_("debian/rules uses dh meson debian/build"), "varies", izeable=True),
    StdRule("ZL0014", "debian.copyright", N_("debian/copyright mentions AGPL"), "varies", izeable=True),
    StdRule("ZL0015", "debian.source.format", N_("debian/source/format native 3.0"), "ok", izeable=True),
    StdRule("ZL0016", "debian.VERSION_sync", N_("VERSION matches debian/changelog"), "varies", izeable=True),
    StdRule("ZL0017", "debian.Depends.bash-shlib", N_("bash package Depends includes bash-shlib"), "varies", izeable=True),
    StdRule("ZL0018", "meson.project", N_("meson.build project() call"), "varies", izeable=True),
    StdRule("ZL0019", "meson.license", N_("meson license AGPL-3.0-or-later"), "varies", izeable=True),
    StdRule("ZL0020", "meson.project_*", N_("meson project_author/email/year"), "varies", izeable=True),
    StdRule("ZL0021", "meson.version_source", N_("Meson version from zfr version"), "varies", izeable=True),
    StdRule("ZL0022", "meson.version_fallback", N_("Meson 0.0.0 version fallback"), "varies", izeable=True),
    StdRule("ZL0023", "meson.asciidoctor", N_("Meson invokes asciidoctor for man pages"), "varies", izeable=True),
    StdRule("ZL0024", "meson.look", N_("Meson run_target look DESTDIR preview"), "varies", izeable=True),
    StdRule("ZL0025", "meson.completion_install", N_("Meson installs bash-completion"), "varies", izeable=True),
    StdRule("ZL0026", "rpm.missing", N_("Optional packaging/rpm/*.spec next to debian/"), "note", izeable=True),
    StdRule("ZL0027", "rpm.topdir.local", N_("packaging/rpm/Makefile uses project-local rpmbuild"), "error", izeable=True),
    StdRule("ZL0028", "rpm.topdir", N_("packaging/rpm/Makefile TOPDIR uses %_topdir"), "ok", izeable=True),
    StdRule("ZL0029", "rpm.topdir.clean", N_("packaging/rpm/Makefile clean removes entire TOPDIR"), "error", izeable=True),
    StdRule("ZL0030", "rpm.topdir.leftover", N_("Project-local rpmbuild/ directory"), "warn", izeable=True),
    StdRule("ZL0031", "rpm.dynamic_version", N_("RPM spec Version from zfr version"), "varies", izeable=True),
    StdRule("ZL0032", "rpm.license", N_("RPM spec License AGPL-3.0-or-later"), "varies", izeable=True),
    StdRule("ZL0033", "rpm.URL", N_("RPM spec URL matches debian Homepage"), "warn", izeable=True),
    StdRule("ZL0034", "rpm.Summary", N_("RPM spec Summary matches debian Description"), "warn", izeable=True),
    StdRule("ZL0035", "rpm.build", N_("RPM spec builds with Meson not autotools"), "varies", izeable=True),
    StdRule("ZL0036", "rpm.makefile.version", N_("packaging/rpm/Makefile calls zfr version"), "varies", izeable=True),
    StdRule("ZL0037", "rpm.makefile", N_("packaging/rpm/Makefile convenience targets"), "note", izeable=True),
    StdRule("ZL0038", "rpm.Requires.bash-shlib", N_("bash RPM spec Requires bash-shlib"), "error", izeable=True),
    StdRule("ZL0039", "rpm.substvar", N_("RPM Requires without Debian substvars"), "error", izeable=True),
    StdRule("ZL0040", "rpm.noarch.elf", N_("noarch RPM with Meson executable()"), "error", izeable=True),
    StdRule("ZL0041", "rpm.debug_package.elf", N_("debug_package %{nil} on ELF package"), "warn", izeable=True),
    StdRule("ZL0042", "rpm.noarch.script", N_("Script-only RPM needs BuildArch: noarch"), "error", izeable=True),
    StdRule("ZL0043", "rpm.files.puff", N_("RPM %files lists template puff placeholder"), "error", izeable=True),
    StdRule("ZL0044", "rpm.files.mo", N_("RPM %files covers gettext .mo catalogs"), "varies", izeable=True),
    StdRule("ZL0045", "rpm.files.locale_man", N_("RPM %files covers locale man pages"), "varies", izeable=True),
    StdRule("ZL0046", "rpm.files.setup", N_("RPM %files covers datadir/setup scripts"), "varies", izeable=True),
    StdRule("ZL0047", "rpm.files.meson", N_("RPM %files covers Meson install paths"), "varies", izeable=True),
    StdRule("ZL0048", "rpm.files.spurious_pkgdata", N_("RPM %files spurious package data path"), "error", izeable=True),
    StdRule("ZL0049", "rpm.files.completion_basename", N_("RPM completion basename matches Meson"), "error", izeable=True),
    StdRule("ZL0050", "i18n.l10n-level", N_("Configured l10n coverage level"), "ok"),
    StdRule("ZL0051", "i18n.po", N_("Optional po/ gettext directory"), "note", izeable=True),
    StdRule("ZL0052", "i18n.linguas", N_("po/LINGUAS present when po/ exists"), "warn", izeable=True),
    StdRule("ZL0053", "i18n.linguas.coverage", N_("LINGUAS covers required locales"), "varies", izeable=True),
    StdRule("ZL0054", "i18n.po.files", N_("LINGUAS entries have matching .po files"), "varies", izeable=True),
    StdRule("ZL0055", "i18n.man.coverage", N_("Whole-document man translations for level"), "varies"),
    StdRule("ZL0056", "i18n.man.english-copy", N_("Translated man still has English Name line"), "warn"),
    StdRule("ZL0057", "identity.*", N_("Directory name matches packaging identity"), "varies"),
    StdRule("ZL0058", "identity.meson.project", N_("meson project name"), "ok"),
    StdRule("ZL0059", "identity.source_vs_meson", N_("debian Source matches meson project name"), "warn"),
    StdRule("ZL0060", "identity.debian.Source", N_("debian Source field"), "ok"),
    StdRule("ZL0061", "identity.rpm.Name", N_("RPM spec Name matches package name"), "varies", izeable=True),
    StdRule("ZL0062", "lang.shared.name", N_("Legacy example shared module name"), "warn"),
    StdRule("ZL0063", "lang.shared.example", N_("Template-only shared example module"), "note"),
    StdRule("ZL0064", "lang.bash.src", N_("Bash src/*.in scripts"), "varies"),
    StdRule("ZL0065", "lang.tests", N_("tests/ directory for C/C++ templates"), "varies"),
    StdRule("ZL0066", "lang.cobol.tests", N_("COBOL tests/ directory"), "varies"),
    StdRule("ZL0067", "lang.fortran.tests", N_("Fortran tests/ directory"), "varies"),
    StdRule("ZL0068", "lang.pascal.tests", N_("Pascal tests/ directory"), "varies"),
    StdRule("ZL0069", "lang.d.tests", N_("D tests/ directory"), "varies"),
    StdRule("ZL0070", "lang.kotlin.tests", N_("Kotlin tests/ directory"), "varies"),
    StdRule("ZL0071", "lang.nim.tests", N_("Nim tests/ directory"), "varies"),
    StdRule("ZL0072", "lang.lua.tests", N_("Lua tests/ directory"), "varies"),
    StdRule("ZL0073", "lang.python.tests", N_("Python tests/ directory"), "varies"),
    StdRule("ZL0074", "lang.zig.build", N_("Zig build.zig present"), "error"),
    StdRule("ZL0075", "lang.rust.cargo", N_("Rust Cargo.toml present"), "error"),
    StdRule("ZL0076", "lang.go.mod", N_("Go go.mod present"), "error"),
    StdRule("ZL0077", "tokens.template", N_("Template puff tokens expected in meta/template"), "ok"),
    StdRule("ZL0078", "tokens.leftover", N_("No leftover zephyr/some_puff1 tokens in apps"), "varies"),
    StdRule("ZL0079", "template.coverage", N_("Language template structural files present"), "varies", izeable=True),
    StdRule("ZL0080", "readme.placeholder.*", N_("README still has template placeholder banner"), "varies"),
    StdRule("ZL0081", "readme.*", N_("README has no template banner"), "ok"),
    StdRule(
        "ZL0082",
        "i18n.po.wrap",
        N_("gettext .po catalogs use --no-wrap (no line wrapping)"),
        "warn",
        izeable=True,
    ),
    StdRule(
        "ZL0083",
        "layout.gitignore*",
        N_("Root and component .gitignore coverage (node_modules/, dist/, backend/src/generated/, …)"),
        "varies",
    ),
    StdRule(
        "ZL0084",
        "meson.foreach_puff",
        N_("At most one foreach puff man-page loop in meson.build"),
        "varies",
        izeable=True,
    ),
    StdRule(
        "ZL0085",
        "lang.c.bas.main",
        N_("C-family main uses bas i18n.h/env.h, self_exe, init_i18n(LOCALEDIR)"),
        "varies",
        izeable=True,
    ),
    StdRule(
        "ZL0086",
        "lang.c.bas.logger",
        N_("C-family sources define_logger() via bas/log/deflog.h"),
        "varies",
        izeable=True,
    ),
    StdRule(
        "ZL0087",
        "lang.c.bas.localedir",
        N_("meson config.h defines LOCALEDIR for init_i18n"),
        "varies",
        izeable=True,
    ),
    StdRule(
        "ZL0088",
        "lang.c.bas.gettext_space",
        N_("gettext _() strings must not have leading/trailing spaces"),
        "warn",
        izeable=True,
    ),
    StdRule(
        "ZL0089",
        "i18n.po.quality",
        N_("gettext .po completion (msgid-copy counts as untranslated; ≤20% ≈ missing)"),
        "varies",
    ),
    StdRule(
        "ZL0090",
        "source.hardcoded.path",
        N_("Hardcoded FHS install paths in sources (use @DATADIR@ / configure_file)"),
        "warn",
        izeable=True,
    ),
    StdRule(
        "ZL0091",
        "source.hardcoded.version",
        N_("Hardcoded project version in sources (use @VERSION@ / PROJECT_VERSION)"),
        "warn",
        izeable=True,
    ),
    StdRule(
        "ZL0092",
        "source.hardcoded",
        N_("No hardcoded install paths or project version strings"),
        "ok",
    ),
    StdRule(
        "ZL0093",
        "i18n.po.placeholder",
        N_("gettext .po empty msgstr or omitted msgid-copy (keep-English field literals exempt)"),
        "warn",
    ),
    StdRule(
        "ZL0094",
        "meson.version_subst",
        N_("Project version substituted by Meson config and used in at least one source"),
        "varies",
        izeable=True,
        detail=(
            "meson.build should feed VERSION/PROJECT_VERSION via configuration_data "
            "(ize_cfg / config_h / paths_cfg), and at least one source under src/ "
            "(or a configure_file input) must consume @VERSION@ or PROJECT_VERSION."
        ),
    ),
    StdRule(
        "ZL0095",
        "layout.posync",
        N_("posync run_target is externalized as scripts/posync.sh"),
        "varies",
        izeable=True,
        detail=(
            "When po/ exists, meson.run_target('posync') must call scripts/posync.sh "
            "rather than an inline bash -euc heredoc. Run `zfr ize` to extract."
        ),
    ),
    StdRule(
        "ZL0096",
        "layout.scripts",
        N_("Build/deploy/maintenance scripts live under scripts/"),
        "varies",
        izeable=True,
        detail=(
            "Root-level *.sh helpers and meson run_target bodies for look / "
            "install-symlinks / uninstall-symlinks / posync / deploy belong in "
            "scripts/. Run `zfr ize` to move and rewire."
        ),
    ),
    StdRule(
        "ZL0097",
        "debian.Description",
        N_("debian/control extended Description present"),
        "varies",
        izeable=True,
    ),
    StdRule(
        "ZL0098",
        "debian.Priority",
        N_("debian/control Priority field"),
        "varies",
        izeable=True,
    ),
    StdRule(
        "ZL0099",
        "ci.release_workflow",
        N_("GitHub Actions release-packages workflow (Docker matrix, no nested deps)"),
        "varies",
        izeable=True,
        detail=(
            "Expect .github/workflows/release-packages.yml triggered on release "
            "published, plus scripts/ci helpers. Peer deps use scripts/ci/deps.conf "
            "and install-only fetch (never nested-build). Apt component is main."
        ),
    ),
    StdRule(
        "ZL0100",
        "ci.release_scripts",
        N_("scripts/ci helpers for multi-distro package builds"),
        "varies",
        izeable=True,
    ),
    StdRule(
        "ZL0101",
        "ci.matrix_arch",
        N_("CI matrix arch policy (raspi armhf/v6; uos/kylin loong64-only)"),
        "varies",
        izeable=True,
        detail=(
            "armhf only for raspi_* with platform linux/arm/v6 (not Debian armhf "
            "ARMv7). loong64 only for uos_*/kylin_*. Debian/Ubuntu use "
            "amd64/arm64/riscv64."
        ),
    ),
    StdRule(
        "ZL0102",
        "ci.rpm_deb_deps",
        N_("RPM CI maps Debian Build-Depends (bash-builtins → bash)"),
        "varies",
        izeable=True,
        detail=(
            "When translating debian/control Build-Depends into rpmbuild, apply "
            "experiential mappings: bash-builtins is provided by bash (bash.pc "
            "aliased to bash-builtins.pc); libglib2.0-dev → glib2-devel; etc."
        ),
    ),
)

LINT_RULES = RuleRegistry(_LINT_RULES)


def lint_rule_id(code: str) -> str:
    return LINT_RULES.rule_id(code)
