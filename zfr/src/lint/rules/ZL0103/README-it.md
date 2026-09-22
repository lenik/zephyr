# packaging/rpm/*.patch collegato come PatchN + %autosetup/%patch

Le patch solo-RPM sotto packaging/rpm/*.patch devono essere elencate come PatchN: nello spec e applicate in %prep (%autosetup -p1 o %patch -PN -p1). Makefile e build-rpm.sh le copiano in SOURCES.

### RPM deve rispecchiare Meson/Debian

%files, BuildArch e Version dello spec devono descrivere lo stesso payload che Meson installa. TOPDIR rpmbuild locale al progetto e elenchi file obsoleti sono modalità di fallimento comuni.


### Questo controllo: {title}

{detail}
Suggerimento di gravità: {sev}.


### Conseguenze tipiche

File non pacchettizzati, noarch/ELF sbagliato, rpmbuild/ residuo, o substvars Debian copiati in Requires.
