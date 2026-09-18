## ZL0001

### I file lunghi ostacolano ownership

Sorgenti molto lunghe sono difficili da revisionare, testare e possedere. Zephyr preferisce moduli coesi sotto un pacchetto con entry sottile.


### Cosa migliora

Diff più piccoli, confini chiari, test più facili, meno conflitti di merge.


### Soglie

Lint conta righe non vuote (salta build/debian/po/…). Nota ~600, avviso ~1000. Esempi template saltati.


### Fix manuale

Dividi e aggiorna meson/install/import. `zfr ize` non divide in automatico.


## ZL0095
### posync inline è ingestibile

Un heredoc bash -euc in meson.build si duplica e si debugga male. Contratto: `zfr translate --sync` da run_target('posync').


### Vantaggio

Un comando sincronizza xgettext/msgmerge; ninja posync resta corto; CI chiama `zfr translate --sync` o importa.


### Solve

Ize collega posync a translate --sync. Poi verifica POTFILES.


## ZL0096
### Gli script di manutenzione stanno in scripts/

install-symlinks/deploy in root sporcano il packaging. Sync e anteprima DESTDIR: `zfr translate --sync` e `zfr build --look`.


### Rilevamento

Segnala *.sh in root e run_target inline da esternalizzare o sostituire con sottocomandi zfr.


### Dopo lo spostamento

Aggiorna docs/CI. Solve riscrive Meson verso scripts/… o zfr.
