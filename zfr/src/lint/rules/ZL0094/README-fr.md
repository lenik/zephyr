# Version de projet substituée par la config Meson et utilisée dans au moins une source

meson.build doit alimenter VERSION/PROJECT_VERSION via configuration_data (ize_cfg / config_h / paths_cfg), et au moins une source sous src/ (ou une entrée configure_file) doit consommer @VERSION@ ou PROJECT_VERSION.

### Une substitution sans consommateur est incomplète

Meson doit à la fois définir VERSION/PROJECT_VERSION et avoir des sources qui le lisent vraiment — sinon les binaires empaquetés mentent encore.


### Comment c'est vérifié

Cherche les clés configuration_data et l'usage de @VERSION@ / PROJECT_VERSION dans les sources installées.


### Fermer la boucle

Ajoutez la moitié manquante (subst ou consommateur). Solve mappe vers les étapes ize subst quand disponibles.
