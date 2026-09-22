# RPM CI maps Debian Build-Depends; RPM-only patches via %patch

When translating debian/control Build-Depends into rpmbuild, apply experiential mappings: bash-builtins → bash (ships bash.pc). RPM-only source tweaks live in packaging/rpm/*.patch and are applied with PatchN + %autosetup/%patch (build-rpm copies them to SOURCES); do not mutate system .pc files in the container.

### {title}

Rule {id} (`{code}`) is part of the zephyr packaging/
      layout contract. Default severity hint: {sev}.


### What lint does

{detail}
      Implemented under `{code}` in `zfr lint`. Findings carry
      a concrete fix string when possible. Remap severity with
      `-w` / `-e` / `--strict`.


### Changing the tree

Fixes may touch packaging, meson.build, sources, or scaffold
      copies. Diff Maintainer, Depends, %files, and *.in scripts
      before upload.
