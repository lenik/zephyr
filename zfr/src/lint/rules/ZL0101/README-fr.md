# Politique d'arch de la matrice CI (debian armhf/v7 ; raspi armhf/v6 ; uos/kylin loong64)

Debian armhf utilise linux/arm/v7 ; raspi_* utilise linux/arm/v6. loong64 seulement pour uos_*/kylin_*. Ubuntu peut ajouter i386/amd64v3 ; aussi des sections de matrice mingw/cygwin pour les builds natifs Windows.

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
