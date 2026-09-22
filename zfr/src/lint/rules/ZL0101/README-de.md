# CI-Matrix-Arch-Richtlinie (debian armhf/v7; raspi armhf/v6; uos/kylin loong64)

Debian armhf nutzt linux/arm/v7; raspi_* nutzt linux/arm/v6. loong64 nur für uos_*/kylin_*. Ubuntu kann i386/amd64v3 ergänzen; außerdem mingw/cygwin-Matrixabschnitte für native Windows-Builds.

### {title}

Regel {id} (`{code}`) gehört zum zephyr packaging/
Layout-Vertrag. Standard-Schweregrad-Hinweis: {sev}.

### Was lint tut

{detail}
Implementiert unter `{code}` in `zfr lint`. Befunde tragen
wenn möglich einen konkreten Fix-Text. Schweregrad umbiegen mit
`-w` / `-e` / `--strict`.

### Beim Ändern des Baums

Fixes können packaging, meson.build, Quellen oder Scaffold-
Kopien berühren. Diffen Sie Maintainer, Depends, %files und *.in-Skripte vor dem Upload.
