## ZL0001

### Les fichiers longs nuisent à l'ownership

Les sources très longues sont dures à relire, tester et posséder. Zephyr préfère des modules cohérents sous un paquet avec une entrée fine.


### Ce que ça apporte

Diffs plus petits, frontières claires, tests unitaires plus faciles, moins de conflits de merge.


### Seuils

Lint compte les lignes non vides (hors build/debian/po/…). Note ~600, avertissement ~1000. Les exemples de modèle sont ignorés.


### Correction manuelle

Découpez et mettez à jour meson/install/imports. `zfr ize` ne découpe pas automatiquement.


## ZL0095
### posync en ligne est intenable

Un heredoc bash -euc dans meson.build se duplique et se débogue mal. Contrat : `zfr translate --sync` depuis run_target('posync').


### Gain

Une commande synchronise xgettext/msgmerge ; ninja posync reste court ; CI appelle `zfr translate --sync` ou importe le module.


### Solve

Ize rebranche posync sur translate --sync. Vérifiez POTFILES ensuite.


## ZL0096
### Les scripts d'entretien vont sous scripts/

install-symlinks/deploy à la racine encombrent le packaging. Sync et aperçu DESTDIR : `zfr translate --sync` et `zfr build --look`.


### Détection

Signale les *.sh racine et les run_target inline à externaliser ou remplacer par des sous-commandes zfr.


### Après déplacement

Mettez à jour docs/CI. Solve réécrit Meson vers scripts/… ou zfr.
