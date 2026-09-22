# RPM %files copre le man page di locale

### RPM deve rispecchiare Meson/Debian

%files, BuildArch e Version dello spec devono descrivere lo stesso payload che Meson installa. TOPDIR rpmbuild locale al progetto e elenchi file obsoleti sono modalità di fallimento comuni.


### Questo controllo: {title}

{detail}
Suggerimento di gravità: {sev}.


### Conseguenze tipiche

File non pacchettizzati, noarch/ELF sbagliato, rpmbuild/ residuo, o substvars Debian copiati in Requires.
