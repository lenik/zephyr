# Le CI RPM mappe les Build-Depends Debian ; correctifs RPM-only via %patch

En traduisant les Build-Depends de debian/control vers rpmbuild, appliquez des correspondances empiriques : bash-builtins → bash (fournit bash.pc). Les ajustements de sources RPM-only vivent dans packaging/rpm/*.patch et s'appliquent avec PatchN + %autosetup/%patch (build-rpm les copie vers SOURCES) ; ne mutilez pas les .pc système dans le conteneur.

### {title}

La règle {id} (`{code}`) fait partie du contrat de
disposition packaging/ de zephyr. Indice de sévérité par défaut : {sev}.

### Ce que fait lint

{detail}
Implémenté sous `{code}` dans `zfr lint`. Les constats portent
quand possible une chaîne de correction concrète. Remappez la sévérité avec
`-w` / `-e` / `--strict`.

### En modifiant l'arborescence

Les correctifs peuvent toucher packaging, meson.build, les sources ou des copies
d'échafaudage. Comparez Maintainer, Depends, %files et les scripts *.in avant l'envoi.
