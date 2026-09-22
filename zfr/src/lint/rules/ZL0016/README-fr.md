# VERSION correspond à debian/changelog

### Une seule source de vérité

`VERSION` doit correspondre à la dernière entrée de `debian/changelog`. Le `.githooks/pre-commit` standard (avec `core.hooksPath=.githooks`) réécrit `VERSION` au commit.


### Quand un hook de sync est configuré

Si ce hook pre-commit est présent et synchronise VERSION depuis le changelog, un décalage temporaire jusqu'au prochain commit est attendu — lint rapporte **ok** au lieu d'un avertissement.


### Quand aucun hook n'est configuré

Un décalage est un **warn** : alignez VERSION à la main ou installez le hook standard via `zfr ize`, puis `git config core.hooksPath .githooks`.
