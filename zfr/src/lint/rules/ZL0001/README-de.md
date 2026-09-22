# Quelldateilänge; in Unterverzeichnis des Pakets extrahieren

### Lange Dateien erschweren Ownership

Sehr lange Quelldateien sind schwer zu reviewen, zu testen und zu verantworten. Zephyr bevorzugt kohäsive Module — oft unter einem Paket-Unterverzeichnis mit einer dünnen Einstiegsdatei (dieselbe Form, die create/ize erwarten). Ein Unterverzeichnis ist optional: wenn Helfer anders ausgelagert werden und das Ergebnis wartbar bleibt, ist das in Ordnung.


### Was Verbesserung bringt

Kleinere Review-Diffs, klarere Modulgrenzen, einfachere Unit-Tests und weniger Merge-Konflikte auf stark bearbeiteten Dateien.


### Schwellen

Lint zählt nicht-leere Zeilen (build/debian/po/… ausgelassen). Ein Hinweis erscheint bei ~600 Zeilen; eine Warnung bei ~1000. Template-Beispielmodule werden übersprungen. Pfade, die zu einer nahen `.lintignore` passen (gitignore-Stil; darf in jedem Unterverzeichnis liegen), werden übersprungen — Sprachvorlagen ignorieren `*.css` standardmäßig.


### Beheben ist manuell

Teilen oder extrahieren Sie kohäsive Abschnitte und aktualisieren Sie meson-/Install-/Import-Listen selbst. `zfr ize` splittet Quellen nicht automatisch.
