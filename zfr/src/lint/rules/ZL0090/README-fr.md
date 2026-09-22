# Chemins d'installation FHS en dur dans les sources (utiliser @DATADIR@ / configure_file)

### Un /usr en dur casse les préfixes

Les chemins FHS absolus (/usr/share, /usr/bin, …) échouent sous DESTDIR, préfixes non standard et le staging Meson configure_file.


### Forme préférée

Les scripts utilisent @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (ou équivalent) et sont installés depuis *.in via Meson.


### Ce que fait Solve

Ize renomme les scripts concernés en *.in et câble configure_file. Revérifiez les shebangs et les tests qui supposaient des chemins vivants.
