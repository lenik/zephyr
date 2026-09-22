# VERSION corrisponde a debian/changelog

### Un'unica fonte di verità

`VERSION` dovrebbe corrispondere all'ultima voce di `debian/changelog`. Il `.githooks/pre-commit` standard (con `core.hooksPath=.githooks`) riscrive `VERSION` al commit.


### Quando un hook di sync è configurato

Se quel hook pre-commit è presente e sincronizza VERSION dal changelog, una discrepanza temporanea fino al prossimo commit è attesa — lint riporta **ok** invece di un avviso.


### Quando nessun hook è configurato

Una discrepanza è un **warn**: allineate VERSION a mano o installate l'hook standard via `zfr ize`, poi `git config core.hooksPath .githooks`.
