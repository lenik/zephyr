# Build/deploy/maintenance scripts live under scripts/

### Gli script di manutenzione stanno in scripts/

install-symlinks/deploy in root sporcano il packaging. Sync e anteprima DESTDIR: `zfr translate --sync` e `zfr build --look`.


### Rilevamento

Segnala *.sh in root e run_target inline da esternalizzare o sostituire con sottocomandi zfr.


### Dopo lo spostamento

Aggiorna docs/CI. Solve riscrive Meson verso scripts/… o zfr.
