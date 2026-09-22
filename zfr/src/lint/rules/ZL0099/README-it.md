# Workflow GitHub Actions release-packages (matrice Docker, senza dipendenze annidate)

Aspettatevi .github/workflows/release-packages.yml attivato su release published, più helper in scripts/ci. Le peer dep usano scripts/ci/deps.conf e fetch solo-installazione (mai nested-build). Il componente Apt è main.

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
