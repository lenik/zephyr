# Il run_target posync è esternalizzato come scripts/posync.sh

Quando esiste po/, meson.run_target('posync') deve chiamare scripts/posync.sh invece di un heredoc bash -euc in linea. Eseguite `zfr ize` per estrarre.

### Un posync in linea è immantenibile

Un heredoc bash -euc in meson.build si duplica tra i template ed è doloroso da debuggare. Il contratto è `zfr translate --sync` (Python) collegato da run_target('posync'), non un heredoc in linea.


### Guadagno

Un comando sincronizza xgettext/msgmerge in locale; ninja posync resta breve; la CI può chiamare `zfr translate --sync` o importare `translate.sync`.


### Solve

Ize riscrive run_target('posync') per invocare translate --sync tramite l'ingresso Python del progetto (import-first in zfr). Verificate poi POTFILES e i flag di lingua.
