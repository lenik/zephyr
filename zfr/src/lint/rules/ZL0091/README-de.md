# Hartcodierte Projektversion in Quellen (nutze @VERSION@ / PROJECT_VERSION)

### Versionsliterale driften

Ein hart codierter Release-String weicht von debian/changelog und Meson project_version() ab, sobald Sie bump'en.


### Eine Wahrheitsquelle

Bevorzugen Sie zur Build-Zeit ersetzte @VERSION@ / PROJECT_VERSION, damit `--version`, Wrapper und Pakete übereinstimmen.


### Risiken beim Umstellen

C/C++ braucht meist config.h; Skripte brauchen *.in. Vor dem Schreiben auf großen Bäumen ize trocken laufen lassen (`-n`).
