# Build/deploy/maintenance scripts live under scripts/

Root-level *.sh helpers and meson run_target bodies for look / install-symlinks / uninstall-symlinks / posync / deploy belong in scripts/. Run `zfr ize` to move and rewire.

### Maintenance scripts belong under scripts/

install-symlinks / deploy helpers at the repo root clutter the packaging surface. Zephyr keeps those under scripts/. Catalog sync and DESTDIR preview are `zfr translate --sync` and `zfr build --look` instead of bespoke posync.sh/look.sh when possible.


### Detection

Flags root *.sh maintenance names and inline run_target bodies that should be externalized or replaced with zfr subcommands.


### After moving

Update docs and any CI that called the old paths. Solve rewrites Meson run_targets to scripts/… or zfr translate/build.
