# packaging/rpm/*.patch wired as PatchN + %autosetup/%patch

RPM-only patches under packaging/rpm/*.patch must be listed as PatchN: in the spec and applied in %prep (%autosetup -p1 or %patch -PN -p1). Makefile and build-rpm.sh copy them into SOURCES.

### RPM must mirror Meson/Debian

spec %files, BuildArch, and Version have to describe the same payload Meson installs. Project-local rpmbuild TOPDIR and stale file lists are common failure modes.


### This check: {title}

{detail}
      Severity hint: {sev}.


### Typical fallout

Unpackaged files, wrong noarch/ELF, leftover rpmbuild/, or Debian substvars copied into Requires.
