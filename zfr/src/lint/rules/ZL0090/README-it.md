# Percorsi di installazione FHS hardcoded nelle sorgenti (usa @DATADIR@ / configure_file)

### Un /usr cablato rompe i prefissi

I percorsi FHS assoluti (/usr/share, /usr/bin, …) falliscono sotto DESTDIR, prefissi non standard e lo staging Meson configure_file.


### Forma preferita

Gli script usano @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (o equivalenti) e si installano da *.in via Meson.


### Cosa fa Solve

Ize rinomina gli script interessati in *.in e collega configure_file. Ricontrollate shebang e test che assumevano percorsi live.
