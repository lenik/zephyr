# Quelldateilänge; in Unterverzeichnis des Pakets extrahieren

### Lange Dateien kämpfen um Eigentum

Sehr lange Quelldateien sind schwer zu überprüfen, zu testen und zu besitzen. Zephyr bevorzugt zusammenhängende Module – oft unter einem Unterverzeichnis eines Pakets mit einer dünnen Einstiegspunktdatei (die gleiche Struktur, die create/ize erwartet wird). Ein Unterverzeichnis ist optional: Wenn Hilfsfunktionen auf andere Weise ausgelagert werden und das Ergebnis wartbar ist, ist das in Ordnung.


### Was die Verbesserung Ihnen bringt

Kleinere Überprüfungsunterschiede, klarere Modulgrenzen, einfachere Unit-Tests und weniger Merge-Konflikte bei stark frequentierten Dateien.


### Schwellenwerte

Lint zählt nicht-leere Zeilen (überspringt build/debian/po/…). Eine Anmerkung erscheint bei etwa 600 Zeilen; eine Warnung bei etwa 1000. Beispiel-Template-Module werden übersprungen. Pfade, die mit einer nahegelegenen `.lintignore` übereinstimmen (gitignore-Stil; kann in jedem Unterverzeichnis liegen), werden übersprungen — Sprach-Templates liefern standardmäßig `*.css`, das ignoriert wird.


### Das Beheben ist manuell

Teilen oder extrahieren Sie zusammenhängende Abschnitte und aktualisieren Sie selbst die Listen für Meson/Install/Import. `zfr ize` teilt Quellen nicht automatisch.
