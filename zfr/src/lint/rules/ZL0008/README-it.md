# voce debian/control Build-Depends

### Debian è il contratto APT

controllo/regole/copyright/formato sorgente decidono come viene creato il pacchetto e cosa installano gli utenti. Zephyr è standardizzato su Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### Questo assegno: {title}

{dettaglio}
Suggerimento di gravità predefinito: {sev}.


### Perché è importante

Un'architettura errata, dei Build-Depend mancanti o un file di regole non Meson non riescono a decostruire o producono pacchetti non caricabili anche quando le compilazioni locali hanno esito positivo.


### Durante la modifica del packaging

Ize può riscrivere dai modelli: confronta sempre Manutentore, Dipende e Architettura prima del caricamento.
