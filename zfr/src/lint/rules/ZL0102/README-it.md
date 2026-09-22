# Il CI RPM mappa i Build-Depends Debian; patch solo RPM via %patch

Nel tradurre i Build-Depends di debian/control in rpmbuild, applicate mappature empiriche: bash-builtins → bash (fornisce bash.pc). Le modifiche sorgente solo-RPM vivono in packaging/rpm/*.patch e si applicano con PatchN + %autosetup/%patch (build-rpm le copia in SOURCES); non mutate i .pc di sistema nel contenitore.

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
