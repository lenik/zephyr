# Helper scripts/ci per build di pacchetti multi-distro

### {title}

La regola {id} (`{code}`) fa parte del contratto di
layout packaging/ di zephyr. Suggerimento di gravità predefinito: {sev}.

### Cosa fa lint

{detail}
Implementato sotto `{code}` in `zfr lint`. I rilievi portano
quando possibile una stringa di correzione concreta. Riassegna la gravità con
`-w` / `-e` / `--strict`.

### Quando si cambia l'albero

Le correzioni possono toccare packaging, meson.build, sorgenti o copie
di scaffold. Confrontate Maintainer, Depends, %files e gli script *.in prima dell'upload.
