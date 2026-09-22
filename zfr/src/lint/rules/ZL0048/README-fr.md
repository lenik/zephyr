# Chemin de données de paquet superflu dans RPM %files

### RPM doit refléter Meson/Debian

%files, BuildArch et Version du spec doivent décrire la même charge utile que Meson installe. Un TOPDIR rpmbuild local au projet et des listes de fichiers périmées sont des modes d'échec courants.


### Ce contrôle : {title}

{detail}
Indice de sévérité : {sev}.


### Retombées typiques

Fichiers non empaquetés, mauvais noarch/ELF, rpmbuild/ restant, ou substvars Debian copiés dans Requires.
