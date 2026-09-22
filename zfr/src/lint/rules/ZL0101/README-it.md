# Policy arch della matrice CI (debian armhf/v7; raspi armhf/v6; uos/kylin loong64)

Debian armhf usa linux/arm/v7; raspi_* usa linux/arm/v6. loong64 solo per uos_*/kylin_*. Ubuntu può aggiungere i386/amd64v3; anche sezioni di matrice mingw/cygwin per build nativi Windows.

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
