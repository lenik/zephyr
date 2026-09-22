# debian/source/format native 3.0

### Debian è il contratto APT

control / rules / copyright / source format decidono come il pacchetto si costruisce e cosa installano gli utenti. Zephyr standardizza su Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### Questo controllo: {title}

{detail}
Suggerimento di gravità predefinito: {sev}.


### Perché conta

Architecture sbagliata, Build-Depends mancanti o un file rules non-Meson fanno fallire debuild o producono pacchetti non caricabili anche se la compilazione locale riesce.


### Quando si modifica il packaging

Ize può riscrivere dai modelli — confrontate sempre Maintainer, Depends e Architecture prima dell'upload.
