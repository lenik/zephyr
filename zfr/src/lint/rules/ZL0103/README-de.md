# packaging/rpm/*.patch verdrahtet als PatchN + %autosetup/%patch

RPM-only-Patches unter packaging/rpm/*.patch müssen als PatchN: in der Spec stehen und in %prep angewendet werden (%autosetup -p1 oder %patch -PN -p1). Makefile und build-rpm.sh kopieren sie nach SOURCES.

### RPM muss Meson/Debian spiegeln

spec %files, BuildArch und Version müssen dieselbe Nutzlast beschreiben, die Meson installiert. Projektlokales rpmbuild-TOPDIR und veraltete Dateilisten sind häufige Fehlermodi.


### Diese Prüfung: {title}

{detail}
Schweregrad-Hinweis: {sev}.


### Typische Folgen

Ungepackte Dateien, falsches noarch/ELF, übrig gebliebenes rpmbuild/ oder Debian-Substvars, die in Requires kopiert wurden.
