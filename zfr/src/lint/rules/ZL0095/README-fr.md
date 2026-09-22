# Le run_target posync est externalisé en scripts/posync.sh

Quand po/ existe, meson.run_target('posync') doit appeler scripts/posync.sh plutôt qu'un heredoc bash -euc en ligne. Lancez `zfr ize` pour extraire.

### Un posync en ligne est immaintenable

Un heredoc bash -euc dans meson.build se duplique entre modèles et est pénible à déboguer. Le contrat est `zfr translate --sync` (Python) câblé depuis run_target('posync'), pas un heredoc en ligne.


### Gain

Une commande synchronise xgettext/msgmerge localement ; ninja posync reste court ; la CI peut appeler `zfr translate --sync` ou importer `translate.sync`.


### Solve

Ize réécrit run_target('posync') pour invoquer translate --sync via l'entrée Python du projet (import d'abord dans zfr). Vérifiez ensuite POTFILES et les drapeaux de langue.
