# Hartcodierte FHS-Installationspfade in Quellen (nutze @DATADIR@ / configure_file)

### Hartes /usr bricht Präfixe

Absolute FHS-Pfade (/usr/share, /usr/bin, …) scheitern unter DESTDIR, nicht-standard Präfixen und Meson-configure_file-Staging.


### Bevorzugte Form

Skripte nutzen @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (oder Entsprechungen) und werden aus *.in via Meson installiert.


### Was Solve tut

Ize benennt betroffene Skripte in *.in um und verdrahtet configure_file. Shebangs und Tests, die Live-Pfade annahmen, erneut prüfen.
