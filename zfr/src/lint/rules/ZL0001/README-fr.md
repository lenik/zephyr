# Longueur du fichier source ; extraire dans le sous-répertoire du paquet

### Les longs fichiers freinent l'ownership

Les très longs fichiers sources sont durs à relire, tester et posséder. Zephyr préfère des modules cohésifs — souvent sous un sous-répertoire de paquet avec un fichier d'entrée mince (la même forme que create/ize attendent). Un sous-répertoire est optionnel : si les aides sont externalisées autrement et que le résultat reste maintenable, c'est bien.


### Ce que l'amélioration apporte

Des diffs de relecture plus petits, des frontières de modules plus claires, des tests unitaires plus faciles, et moins de conflits de fusion sur les fichiers très actifs.


### Seuils

Lint compte les lignes non vides (en sautant build/debian/po/…). Une note apparaît vers ~600 lignes ; un avertissement vers ~1000. Les modules d'exemple des modèles sont ignorés. Les chemins correspondant à un `.lintignore` voisin (style gitignore ; peut vivre dans n'importe quel sous-répertoire) sont ignorés — les modèles de langage ignorent `*.css` par défaut.


### La correction est manuelle

Découpez ou extrayez des sections cohésives et mettez à jour vous-même les listes meson/install/import. `zfr ize` ne découpe pas automatiquement les sources.
