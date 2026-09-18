## ZL0001

### Lange Dateien erschweren Ownership

Sehr lange Quelldateien sind schwer zu reviewen, zu testen und zuzuordnen. Zephyr bevorzugt zusammenhängende Module unter einem Paketverzeichnis mit dünner Einstiegsdatei.


### Was die Verbesserung bringt

Kleinere Review-Diffs, klarere Modulgrenzen, einfachere Unit-Tests und weniger Merge-Konflikte.


### Schwellen

Lint zählt nicht-leere Zeilen (ohne build/debian/po/…). Hinweis bei ~600, Warnung bei ~1000. Template-Beispiele werden übersprungen.


### Reparatur ist manuell

Datei teilen und meson/Install/Import-Listen selbst aktualisieren. `zfr ize` splittet Quellen nicht automatisch.


## ZL0095
### Inline-posync ist unwartbar

Ein bash -euc-Heredoc in meson.build verdoppelt sich über Templates und ist schwer zu debuggen. Vertrag: `zfr translate --sync` aus run_target('posync').


### Nutzen

Ein Befehl synchronisiert xgettext/msgmerge; ninja posync bleibt kurz; CI ruft `zfr translate --sync` oder importiert `translate.sync`.


### Solve

Ize verdrahtet run_target('posync') auf translate --sync. Danach POTFILES und Sprachflags prüfen.


## ZL0096
### Wartungsskripte gehören unter scripts/

install-symlinks/deploy im Repo-Root verstopfen die Packaging-Oberfläche. Katalog-Sync und DESTDIR-Vorschau: `zfr translate --sync` und `zfr build --look`.


### Erkennung

Markiert Root-*.sh und Inline-run_target-Bodies, die externalisiert oder durch zfr-Unterbefehle ersetzt werden sollten.


### Nach dem Umzug

Docs und CI aktualisieren. Solve schreibt Meson-run_targets auf scripts/… oder zfr translate/build um.
