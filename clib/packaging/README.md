# Optional non-RPM packaging

Platform-specific recipes aligned with `debian/` and `packaging/rpm/`.
Version: `zfr version` (same as `meson.build` and `packaging/rpm/Makefile`).

| Platform | Directory | Build |
|----------|-----------|-------|
| RPM      | rpm/      | `make -C packaging/rpm srpm` |
| Windows  | windows/  | see `windows/README.md` |
| macOS    | macos/    | see `macos/README.md` |
| Arch     | arch/     | see `arch/PKGBUILD` |
| FreeBSD  | freebsd/  | see `freebsd/Makefile` |
