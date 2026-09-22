# noarch RPM with Meson executable()

### RPM must mirror Meson/Debian

spec %files, BuildArch, and Version have to describe the same payload Meson installs. Project-local rpmbuild TOPDIR and stale file lists are common failure modes.


### This check: {title}

{detail}
      Severity hint: {sev}.


### Typical fallout

Unpackaged files, wrong noarch/ELF, leftover rpmbuild/, or Debian substvars copied into Requires.
