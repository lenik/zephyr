# Versione progetto hardcoded nelle sorgenti (usa @VERSION@ / PROJECT_VERSION)

### I letterali di versione divergono

Una stringa di release cablata diverge da debian/changelog e da Meson project_version() non appena fate bump.


### Un'unica fonte di verità

Preferite @VERSION@ / PROJECT_VERSION sostituiti in build così `--version`, wrapper e pacchetti restano allineati.


### Rischi in conversione

C/C++ di solito serve config.h; gli script servono *.in. Fate un dry-run ize (`-n`) sugli alberi grandi prima di scrivere.
