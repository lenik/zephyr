# CI matrix arch policy (debian armhf/v7; raspi armhf/v6; uos/kylin loong64)

Debian armhf uses linux/arm/v7; raspi_* uses linux/arm/v6. loong64 only for uos_*/kylin_*. Ubuntu may add i386/amd64v3; also mingw/cygwin matrix sections for Windows native builds.

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
