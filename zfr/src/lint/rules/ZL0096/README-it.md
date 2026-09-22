# Gli script di build/deploy/manutenzione vivono sotto scripts/

Gli helper *.sh a radice e i corpi meson run_target per look / install-symlinks / uninstall-symlinks / posync / deploy appartengono in scripts/. Eseguite `zfr ize` per spostare e ricollegare.

### Gli script di manutenzione stanno sotto scripts/

Gli helper install-symlinks / deploy alla radice del repo ingombrano la superficie di packaging. Zephyr li tiene sotto scripts/. Sync del catalogo e anteprima DESTDIR sono `zfr translate --sync` e `zfr build --look` invece di posync.sh/look.sh su misura quando possibile.


### Rilevamento

Segnala nomi *.sh di manutenzione a radice e corpi run_target in linea da esternalizzare o sostituire con sottocomandi zfr.


### Dopo lo spostamento

Aggiornate docs e ogni CI che chiamava i vecchi percorsi. Solve riscrive i run_target Meson verso scripts/… o zfr translate/build.
