# VERSION stimmt mit debian/changelog überein

### Eine Wahrheitsquelle

`VERSION` sollte dem neuesten `debian/changelog`-Eintrag entsprechen. Der Standard-`.githooks/pre-commit` (mit `core.hooksPath=.githooks`) schreibt `VERSION` beim Commit um.


### Wenn ein Sync-Hook konfiguriert ist

Ist dieser pre-commit-Hook vorhanden und synchronisiert VERSION aus dem Changelog, ist eine vorübergehende Abweichung bis zum nächsten Commit erwartet — lint meldet **ok** statt Warnung.


### Wenn kein Hook konfiguriert ist

Eine Abweichung ist **warn**: VERSION von Hand angleichen oder den Standard-Hook via `zfr ize` installieren, dann `git config core.hooksPath .githooks`.
