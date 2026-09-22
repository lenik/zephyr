# posync run_target is externalized as scripts/posync.sh

### posync en ligne est intenable

Un heredoc bash -euc dans meson.build se duplique et se débogue mal. Contrat : `zfr translate --sync` depuis run_target('posync').


### Gain

Une commande synchronise xgettext/msgmerge ; ninja posync reste court ; CI appelle `zfr translate --sync` ou importe le module.


### Solve

Ize rebranche posync sur translate --sync. Vérifiez POTFILES ensuite.
