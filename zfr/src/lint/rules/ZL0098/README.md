# debian/control Priority field

### Debian is the APT contract

control / rules / copyright / source format decide how the package builds and what users install. Zephyr standardizes on Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### This check: {title}

{detail}
      Default severity hint: {sev}.


### Why it matters

Wrong Architecture, missing Build-Depends, or a non-Meson rules file fail debuild or produce unloadable packages even when local compiles succeed.


### When editing packaging

Ize may rewrite from templates — always diff Maintainer, Depends, and Architecture before upload.
