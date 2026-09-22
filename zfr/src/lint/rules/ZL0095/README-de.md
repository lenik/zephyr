# posync-run_target ist als scripts/posync.sh ausgelagert

Wenn po/ existiert, muss meson.run_target('posync') scripts/posync.sh aufrufen statt eines Inline-bash -euc-Heredocs. Mit `zfr ize` extrahieren.

### Inline-posync ist unwartbar

Ein bash -euc-Heredoc in meson.build dupliziert sich über Vorlagen und ist schwer zu debuggen. Der Vertrag ist `zfr translate --sync` (Python) von run_target('posync') verdrahtet, kein Inline-Heredoc.


### Nutzen

Ein Befehl synchronisiert xgettext/msgmerge lokal; ninja posync bleibt kurz; CI kann `zfr translate --sync` aufrufen oder `translate.sync` importieren.


### Solve

Ize schreibt run_target('posync') um, damit translate --sync über den Projekt-Python-Einstieg aufgerufen wird (import-first in zfr). Danach POTFILES und Sprachflags prüfen.
