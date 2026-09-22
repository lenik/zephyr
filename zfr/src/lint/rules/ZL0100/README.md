# scripts/ci helpers for multi-distro package builds

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
