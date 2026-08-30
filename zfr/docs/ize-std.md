# Zephyr ize standard (ZI rules)

Numbered steps performed by `zfr ize`. Each change line prints `kind  ZInnn  path  detail`. See also `zfr ize -h`.

| ID | Code | Default | Title |
|----|------|---------|-------|
| ZI001 | `ize.mesonize` | varies | Convert Autotools/CMake with 2meson |
| ZI002 | `ize.scaffold` | varies | Add missing language-template scaffold files |
| ZI003 | `ize.debian.control` | varies | Patch debian/control for zephyr style |
| ZI004 | `ize.debian.rules` | varies | Align debian/rules with Meson dh helper |
| ZI005 | `ize.debian.docs` | varies | Sync debian/docs with installed mans |
| ZI006 | `ize.changelog` | varies | Ensure debian/changelog and VERSION file |
| ZI007 | `ize.hooks` | varies | Install .githooks/pre-commit VERSION sync hook |
| ZI008 | `ize.meson.patch` | varies | Patch meson.build (version, license, docs, completion) |
| ZI009 | `ize.man.convert` | varies | Convert groff man pages to docs/*.adoc |
| ZI010 | `ize.man.stub` | varies | Create AsciiDoc man page stubs |
| ZI011 | `ize.meson.man` | varies | Add Meson asciidoctor man page targets |
| ZI012 | `ize.completion` | varies | Add bash-completion stubs for command puffs |
| ZI013 | `ize.rpm` | varies | Align packaging/rpm/Makefile and RPM spec with debian/Meson |
| ZI014 | `ize.subst` | varies | Replace hardcoded versions with @VERSION@ / config.h |
| ZI015 | `ize.i18n.derive` | varies | Meson build-time derived locale catalogs |
| ZI016 | `ize.i18n.po-nowrap` | varies | Rewrite source .po catalogs without line wrapping |
| ZI017 | `ize.commit` | varies | Bump patch version and git commit (`--commit`) |
| ZI018 | `ize.i18n.coverage` | varies | Ensure `po/LINGUAS` + `.po` for lint l10n level |
| ZI019 | `ize.i18n.man-locale` | varies | Scaffold `docs/<locale>/*.adoc` for lint l10n level |

Suppress rules with `zfr lint -u ID` / `zfr ize -u ID` (comma-separated), or the same flag in `.config/zfr/lint.options` / `.config/zfr/ize.options`.
