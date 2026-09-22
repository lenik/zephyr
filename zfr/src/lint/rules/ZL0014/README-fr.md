# debian/copyright mentionne AGPL

### Debian est le contrat APT

control / rules / copyright / source format décident comment le paquet se construit et ce que les utilisateurs installent. Zephyr standardise sur Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### Ce contrôle : {title}

{detail}
Indice de sévérité par défaut : {sev}.


### Pourquoi c'est important

Une Architecture incorrecte, des Build-Depends manquantes ou un fichier rules non-Meson font échouer debuild ou produisent des paquets inutilisables même si la compilation locale réussit.


### En éditant le packaging

Ize peut réécrire depuis les modèles — comparez toujours Maintainer, Depends et Architecture avant l'envoi.
