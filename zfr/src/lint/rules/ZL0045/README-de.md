# RPM %files deckt Locale-Manpages ab

### RPM muss Meson/Debian spiegeln

spec %files, BuildArch und Version müssen dieselbe Nutzlast beschreiben, die Meson installiert. Projektlokales rpmbuild-TOPDIR und veraltete Dateilisten sind häufige Fehlermodi.


### Diese Prüfung: {title}

{detail}
Schweregrad-Hinweis: {sev}.


### Typische Folgen

Ungepackte Dateien, falsches noarch/ELF, übrig gebliebenes rpmbuild/ oder Debian-Substvars, die in Requires kopiert wurden.
