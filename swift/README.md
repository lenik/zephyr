# zephyr

`zephyr` is a Swift template for small command-line apps, using Meson for build/test/install.
`puff1` is one **example app** in this template; more apps can be added in the same repository.

## Repository layout

- `src/` - Swift source files (`*.swift`)
- `tests/` - Swift smoke/unit tests
- `debian/` - Debian packaging metadata
- `po/` - gettext message catalogs
- `meson.build` - build, test, install, and helper targets

## Example app: `puff1`

`puff1` is a cat-like utility:

```bash
puff1 [OPTION]... [FILE]...
```

- If no `FILE` is provided, it reads from `stdin`.
- If a `FILE` is `-`, it reads from `stdin` at that position.
- Output is written to `stdout`.

Supported options:

- `-v`, `--verbose`
- `-q`, `--quiet`
- `-h`, `--help`
- `--version`

## Build and test

### Build dependencies

```bash
sudo apt install meson ninja-build swiftlang gettext
```

### Configure and build

Use the absolute build directory `/build`:

```bash
meson setup /build
ninja -C /build
```

### Run tests

```bash
meson test -C /build
```

Meson runs a Swift smoke/unit test from `tests/TestCommonLib.swift`.

## i18n (gettext)

`puff1` uses gettext translations under `po/` (`*.po` + generated `.mo` files).

- Installed runtime loads translations from system locale dir.
- Dev runtime (`/build/puff1`) prefers project-local translations from `/build/po` if present.

### Sync translation catalogs

Use `posync` to update catalogs from current source strings:

```bash
ninja -C /build posync
```

`posync` will:

- add missing messages into each language from `po/LINGUAS`
- remove obsolete messages no longer used in source

### Build translation files

```bash
ninja -C /build
```

### Quick locale testing

Prefer `LANGUAGE=<lang>` for predictable gettext selection in dev shells:

```bash
LANGUAGE=ja /build/puff1 -h
LANGUAGE=zh_CN /build/puff1 -h
```

`LANG=<lang>.<encoding>` may depend on whether that locale is generated on your system.

## Install / symlink helpers

Normal install:

```bash
meson install -C /build
```

Debug symlink workflow (under configured prefix):

```bash
ninja -C /build install-symlinks
ninja -C /build uninstall-symlinks
```

## Debian package

```bash
dpkg-buildpackage -us -uc
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**.  
This project explicitly opposes AI exploitation and AI hegemony, and rejects
mindless MIT-style licensing and politically naive BSD-style licensing.  
See `LICENSE` for the full text and supplemental project terms.
