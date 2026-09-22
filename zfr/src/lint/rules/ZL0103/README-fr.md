# packaging/rpm/*.patch branché en PatchN + %autosetup/%patch

Les correctifs RPM-only sous packaging/rpm/*.patch doivent figurer comme PatchN: dans le spec et être appliqués dans %prep (%autosetup -p1 ou %patch -PN -p1). Makefile et build-rpm.sh les copient dans SOURCES.

### RPM doit refléter Meson/Debian

%files, BuildArch et Version du spec doivent décrire la même charge utile que Meson installe. Un TOPDIR rpmbuild local au projet et des listes de fichiers périmées sont des modes d'échec courants.


### Ce contrôle : {title}

{detail}
Indice de sévérité : {sev}.


### Retombées typiques

Fichiers non empaquetés, mauvais noarch/ELF, rpmbuild/ restant, ou substvars Debian copiés dans Requires.
