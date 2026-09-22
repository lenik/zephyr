# RPM-CI mappt Debian-Build-Depends; RPM-only-Patches via %patch

Beim Übersetzen von debian/control Build-Depends nach rpmbuild Erfahrungs-Mappings anwenden: bash-builtins → bash (liefert bash.pc). RPM-only-Quellanpassungen liegen in packaging/rpm/*.patch und werden mit PatchN + %autosetup/%patch angewendet (build-rpm kopiert nach SOURCES); System-.pc-Dateien im Container nicht mutieren.

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
