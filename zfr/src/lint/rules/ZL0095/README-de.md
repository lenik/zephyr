# posync run_target is externalized as scripts/posync.sh

### Inline-posync ist unwartbar

Ein bash -euc-Heredoc in meson.build verdoppelt sich über Templates und ist schwer zu debuggen. Vertrag: `zfr translate --sync` aus run_target('posync').


### Nutzen

Ein Befehl synchronisiert xgettext/msgmerge; ninja posync bleibt kurz; CI ruft `zfr translate --sync` oder importiert `translate.sync`.


### Solve

Ize verdrahtet run_target('posync') auf translate --sync. Danach POTFILES und Sprachflags prüfen.
