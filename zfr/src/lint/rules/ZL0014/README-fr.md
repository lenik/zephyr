# debian/copyright mentionne AGPL

### Debian est le contrat APT

contrôle / règles / droits d'auteur / format source décident de la manière dont le package est construit et de ce que les utilisateurs installent. Zephyr se standardise sur Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### Ce chèque : {title}

{détail}
Indice de gravité par défaut : {sev}.


### Pourquoi c'est important

Une mauvaise architecture, des Build-Depends manquants ou un fichier de règles non Meson échouent à la déconstruction ou produisent des packages non téléchargeables même lorsque les compilations locales réussissent.


### Lors de la modification d'un emballage

Ize peut réécrire à partir de modèles - toujours différer le responsable, les dépendances et l'architecture avant le téléchargement.
