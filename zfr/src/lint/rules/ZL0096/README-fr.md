# Build/deploy/maintenance scripts live under scripts/

### Les scripts d'entretien vont sous scripts/

install-symlinks/deploy à la racine encombrent le packaging. Sync et aperçu DESTDIR : `zfr translate --sync` et `zfr build --look`.


### Détection

Signale les *.sh racine et les run_target inline à externaliser ou remplacer par des sous-commandes zfr.


### Après déplacement

Mettez à jour docs/CI. Solve réécrit Meson vers scripts/… ou zfr.
