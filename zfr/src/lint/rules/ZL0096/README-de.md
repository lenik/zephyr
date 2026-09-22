# Build/deploy/maintenance scripts live under scripts/

### Wartungsskripte gehören unter scripts/

install-symlinks/deploy im Repo-Root verstopfen die Packaging-Oberfläche. Katalog-Sync und DESTDIR-Vorschau: `zfr translate --sync` und `zfr build --look`.


### Erkennung

Markiert Root-*.sh und Inline-run_target-Bodies, die externalisiert oder durch zfr-Unterbefehle ersetzt werden sollten.


### Nach dem Umzug

Docs und CI aktualisieren. Solve schreibt Meson-run_targets auf scripts/… oder zfr translate/build um.
