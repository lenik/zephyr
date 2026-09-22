# scripts/ci-Helfer für Multi-Distro-Paketbuilds

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
