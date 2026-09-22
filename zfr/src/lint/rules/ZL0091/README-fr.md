# Version de projet en dur dans les sources (utiliser @VERSION@ / PROJECT_VERSION)

### Les littéraux de version dérivent

Une chaîne de version en dur diverge de debian/changelog et de Meson project_version() dès que vous bump'ez.


### Une seule source de vérité

Préférez @VERSION@ / PROJECT_VERSION substitués à la construction pour que `--version`, les wrappers et les paquets restent alignés.


### Risques lors de la conversion

C/C++ a souvent besoin de config.h ; les scripts de *.in. Faites un dry-run ize (`-n`) sur les grands arbres avant d'écrire.
