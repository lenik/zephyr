# posync run_target is externalized as scripts/posync.sh

### posync inline è ingestibile

Un heredoc bash -euc in meson.build si duplica e si debugga male. Contratto: `zfr translate --sync` da run_target('posync').


### Vantaggio

Un comando sincronizza xgettext/msgmerge; ninja posync resta corto; CI chiama `zfr translate --sync` o importa.


### Solve

Ize collega posync a translate --sync. Poi verifica POTFILES.
