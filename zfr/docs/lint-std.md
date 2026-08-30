# Zephyr lint standard (ZL rules)

Numbered rules enforced by `zfr lint`. Each finding prints `severity  ZLnnn  code  path`.

| ID | Code | Default | Title |
|----|------|---------|-------|
| ZL001 | `source.long` | varies | Source file length; extract to package subdirectory |
| ZL002 | `source.size` | ok | No oversized source files |
| ZL003 | `layout.*` | varies | Required layout file present or missing |
| ZL004 | `layout.docs` | varies | AsciiDoc man page sources under docs/ |
| ZL005 | `layout.completion` | varies | Bash completion script at project root |
| ZL006 | `layout.VERSION` | varies | VERSION file synced with changelog |
| ZL007 | `layout.pre-commit` | varies | Git pre-commit hook syncs VERSION |
| ZL008 | `debian.build-depends.*` | varies | debian/control Build-Depends entry |
| ZL009 | `debian.debhelper` | varies | debhelper-compat in Build-Depends |
| ZL010 | `debian.Architecture` | varies | debian/control Architecture field |
| ZL011 | `debian.Architecture.elf` | error | ELF binary vs Architecture: all |
| ZL012 | `debian.Homepage` | varies | debian/control Homepage field |
| ZL013 | `debian.rules` | varies | debian/rules uses dh meson debian/build |
| ZL014 | `debian.copyright` | varies | debian/copyright mentions AGPL |
| ZL015 | `debian.source.format` | ok | debian/source/format native 3.0 |
| ZL016 | `debian.VERSION_sync` | varies | VERSION matches debian/changelog |
| ZL017 | `debian.Depends.bash-shlib` | varies | bash package Depends includes bash-shlib |
| ZL018 | `meson.project` | varies | meson.build project() call |
| ZL019 | `meson.license` | varies | meson license AGPL-3.0-or-later |
| ZL020 | `meson.project_*` | varies | meson project_author/email/year |
| ZL021 | `meson.version_source` | varies | Meson version from zfr version |
| ZL022 | `meson.version_fallback` | varies | Meson 0.0.0 version fallback |
| ZL023 | `meson.asciidoctor` | varies | Meson invokes asciidoctor for man pages |
| ZL024 | `meson.look` | varies | Meson run_target look DESTDIR preview |
| ZL025 | `meson.completion_install` | varies | Meson installs bash-completion |
| ZL026 | `rpm.missing` | note | Optional rpm/*.spec next to debian/ |
| ZL027 | `rpm.topdir.local` | error | rpm/Makefile uses project-local rpmbuild |
| ZL028 | `rpm.topdir` | ok | rpm/Makefile TOPDIR uses %_topdir |
| ZL029 | `rpm.topdir.clean` | error | rpm/Makefile clean removes entire TOPDIR |
| ZL030 | `rpm.topdir.leftover` | warn | Project-local rpmbuild/ directory |
| ZL031 | `rpm.dynamic_version` | varies | RPM spec Version from zfr version |
| ZL032 | `rpm.license` | varies | RPM spec License AGPL-3.0-or-later |
| ZL033 | `rpm.URL` | warn | RPM spec URL matches debian Homepage |
| ZL034 | `rpm.Summary` | warn | RPM spec Summary matches debian Description |
| ZL035 | `rpm.build` | varies | RPM spec builds with Meson not autotools |
| ZL036 | `rpm.makefile.version` | varies | rpm/Makefile calls zfr version |
| ZL037 | `rpm.makefile` | note | rpm/Makefile convenience targets |
| ZL038 | `rpm.Requires.bash-shlib` | error | bash RPM spec Requires bash-shlib |
| ZL039 | `rpm.substvar` | error | RPM Requires without Debian substvars |
| ZL040 | `rpm.noarch.elf` | error | noarch RPM with Meson executable() |
| ZL041 | `rpm.debug_package.elf` | warn | debug_package %{nil} on ELF package |
| ZL042 | `rpm.noarch.script` | error | Script-only RPM needs BuildArch: noarch |
| ZL043 | `rpm.files.puff` | error | RPM %files lists template puff placeholder |
| ZL044 | `rpm.files.mo` | varies | RPM %files covers gettext .mo catalogs |
| ZL045 | `rpm.files.locale_man` | varies | RPM %files covers locale man pages |
| ZL046 | `rpm.files.setup` | varies | RPM %files covers datadir/setup scripts |
| ZL047 | `rpm.files.meson` | varies | RPM %files covers Meson install paths |
| ZL048 | `rpm.files.spurious_pkgdata` | error | RPM %files spurious package data path |
| ZL049 | `rpm.files.completion_basename` | error | RPM completion basename matches Meson |
| ZL050 | `i18n.l10n-level` | ok | Configured l10n coverage level |
| ZL051 | `i18n.po` | note | Optional po/ gettext directory |
| ZL052 | `i18n.linguas` | warn | po/LINGUAS present when po/ exists |
| ZL053 | `i18n.linguas.coverage` | varies | LINGUAS covers required locales |
| ZL054 | `i18n.po.files` | varies | LINGUAS entries have matching .po files |
| ZL055 | `i18n.man.coverage` | varies | Whole-document man translations for level |
| ZL056 | `i18n.man.english-copy` | warn | Translated man still has English Name line |
| ZL057 | `identity.*` | varies | Directory name matches packaging identity |
| ZL058 | `identity.meson.project` | ok | meson project name |
| ZL059 | `identity.source_vs_meson` | warn | debian Source matches meson project name |
| ZL060 | `identity.debian.Source` | ok | debian Source field |
| ZL061 | `identity.rpm.Name` | varies | RPM spec Name matches package name |
| ZL062 | `lang.shared.name` | warn | Legacy example shared module name |
| ZL063 | `lang.shared.example` | note | Template-only shared example module |
| ZL064 | `lang.bash.src` | varies | Bash src/*.in scripts |
| ZL065 | `lang.tests` | varies | tests/ directory for C/C++ templates |
| ZL066 | `lang.cobol.tests` | varies | COBOL tests/ directory |
| ZL067 | `lang.fortran.tests` | varies | Fortran tests/ directory |
| ZL068 | `lang.pascal.tests` | varies | Pascal tests/ directory |
| ZL069 | `lang.d.tests` | varies | D tests/ directory |
| ZL070 | `lang.kotlin.tests` | varies | Kotlin tests/ directory |
| ZL071 | `lang.nim.tests` | varies | Nim tests/ directory |
| ZL072 | `lang.lua.tests` | varies | Lua tests/ directory |
| ZL073 | `lang.python.tests` | varies | Python tests/ directory |
| ZL074 | `lang.zig.build` | error | Zig build.zig present |
| ZL075 | `lang.rust.cargo` | error | Rust Cargo.toml present |
| ZL076 | `lang.go.mod` | error | Go go.mod present |
| ZL077 | `tokens.template` | ok | Template puff tokens expected in meta/template |
| ZL078 | `tokens.leftover` | varies | No leftover zephyr/some_puff1 tokens in apps |
| ZL079 | `template.coverage` | varies | Language template structural files present |
| ZL080 | `readme.placeholder.*` | varies | README still has template placeholder banner |
| ZL081 | `readme.*` | ok | README has no template banner |
| ZL082 | `i18n.po.wrap` | warn | gettext .po catalogs use --no-wrap (no line wrapping) |

Suppress rules with `zfr lint -u ID` / `zfr ize -u ID` (comma-separated), or the same flag in `.config/zfr/lint.options` / `.config/zfr/ize.options`.
