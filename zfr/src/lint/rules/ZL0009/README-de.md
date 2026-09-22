# debhelper-compat in Build-Depends

### Debian ist der APT-Vertrag

Kontrolle/Regeln/Copyright/Quellformat entscheiden darüber, wie das Paket erstellt wird und was Benutzer installieren. Zephyr standardisiert auf Meson + dh „--buildsystem=meson --builddirectory=debian/build“.


### Dieser Scheck: {title}

{Detail}
Hinweis zum Standardschweregrad: {Schweregrad}.


### Warum es wichtig ist

Falsche Architektur, fehlende Build-Depends oder eine Nicht-Meson-Regeldatei schlagen beim Debuild fehl oder erzeugen nicht ladbare Pakete, selbst wenn lokale Kompilierungen erfolgreich sind.


### Beim Bearbeiten der Verpackung

Ize kann aus Vorlagen neu schreiben – unterscheiden Sie vor dem Hochladen immer Maintainer, Depends und Architecture.
