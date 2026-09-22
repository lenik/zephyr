# Les scripts build/deploy/maintenance vivent sous scripts/

Les aides *.sh à la racine et les corps meson run_target pour look / install-symlinks / uninstall-symlinks / posync / deploy appartiennent à scripts/. Lancez `zfr ize` pour déplacer et recâbler.

### Les scripts de maintenance appartiennent sous scripts/

Les aides install-symlinks / deploy à la racine du dépôt encombrent la surface de packaging. Zephyr les garde sous scripts/. La sync de catalogues et l'aperçu DESTDIR sont `zfr translate --sync` et `zfr build --look` plutôt que des posync.sh/look.sh sur mesure quand c'est possible.


### Détection

Signale les noms *.sh de maintenance à la racine et les corps run_target en ligne à externaliser ou remplacer par des sous-commandes zfr.


### Après le déplacement

Mettez à jour la doc et toute CI qui appelait les anciens chemins. Solve réécrit les run_targets Meson vers scripts/… ou zfr translate/build.
