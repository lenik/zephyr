# Build-/Deploy-/Wartungsskripte liegen unter scripts/

Root-*.sh-Helfer und meson-run_target-Körper für look / install-symlinks / uninstall-symlinks / posync / deploy gehören nach scripts/. Mit `zfr ize` verschieben und neu verdrahten.

### Wartungsskripte gehören unter scripts/

install-symlinks-/deploy-Helfer an der Repo-Wurzel vermüllen die Packaging-Oberfläche. Zephyr hält sie unter scripts/. Katalog-Sync und DESTDIR-Vorschau sind `zfr translate --sync` und `zfr build --look` statt eigener posync.sh/look.sh, wenn möglich.


### Erkennung

Markiert Root-*.sh-Wartungsnamen und Inline-run_target-Körper, die ausgelagert oder durch zfr-Unterbefehle ersetzt werden sollen.


### Nach dem Verschieben

Docs und CI aktualisieren, die alte Pfade riefen. Solve schreibt Meson-run_targets nach scripts/… oder zfr translate/build um.
