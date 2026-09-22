# Longueur du fichier source ; extraire dans le sous-répertoire du package

### Les fichiers longs se disputent la propriété

Les fichiers source très longs sont difficiles à examiner, tester et à posséder. Zephyr préfère des modules cohésifs — souvent sous un sous-répertoire de package avec un fichier point d'entrée mince (la même forme que create/ize attend). Un sous-répertoire est optionnel : si les aides sont externalisées d'une autre manière et que le résultat est maintenable, cela convient.


### Ce que l'améliorer vous apporte

Diffs de révision plus petits, limites de module plus claires, tests unitaires plus faciles et moins de conflits de fusion sur les fichiers très utilisés.


### Seuils

Lint compte les lignes non vides (en sautant build/debian/po/…). Une note apparaît autour de ~600 lignes ; un avertissement autour de ~1000. Les modules d'exemple de template sont ignorés. Les chemins correspondant à un `.lintignore` proche (style gitignore ; peut se trouver dans n'importe quel sous-répertoire) sont ignorés — les templates de langage incluent `*.css` ignorés par défaut.


### La réparation est manuelle

Divisez ou extrayez vous-même des sections cohésives et mettez à jour les listes meson/install/import. `zfr ize` ne divise pas automatiquement les sources.
