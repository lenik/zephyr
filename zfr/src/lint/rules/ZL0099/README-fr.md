# Workflow GitHub Actions release-packages (matrice Docker, sans deps imbriquées)

Attendez .github/workflows/release-packages.yml déclenché sur release published, plus des aides scripts/ci. Les dépendances paires utilisent scripts/ci/deps.conf et un fetch install-only (jamais de nested-build). Le composant Apt est main.

### {title}

La règle {id} (`{code}`) fait partie du contrat de
disposition packaging/ de zephyr. Indice de sévérité par défaut : {sev}.

### Ce que fait lint

{detail}
Implémenté sous `{code}` dans `zfr lint`. Les constats portent
quand possible une chaîne de correction concrète. Remappez la sévérité avec
`-w` / `-e` / `--strict`.

### En modifiant l'arborescence

Les correctifs peuvent toucher packaging, meson.build, les sources ou des copies
d'échafaudage. Comparez Maintainer, Depends, %files et les scripts *.in avant l'envoi.
