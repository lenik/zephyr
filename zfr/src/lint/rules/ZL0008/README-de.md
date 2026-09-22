# Build-Depends-Eintrag in debian/control

### Debian ist der APT-Vertrag

control / rules / copyright / source format entscheiden, wie das Paket baut und was Nutzer installieren. Zephyr standardisiert auf Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### Diese Prüfung: {title}

{detail}
Standard-Schweregrad-Hinweis: {sev}.


### Warum es zählt

Falsche Architecture, fehlende Build-Depends oder eine Nicht-Meson-rules-Datei lassen debuild scheitern oder erzeugen nicht ladbare Pakete — auch wenn lokale Builds gelingen.


### Beim Bearbeiten des Packaging

Ize kann aus Vorlagen umschreiben — immer Maintainer, Depends und Architecture vor dem Upload diffen.
