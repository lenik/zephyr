# zephyr

`zephyr` is a Nim template for small command-line apps, using Meson for build/test/install.
`some_puff1` is one **example app** in this template; more apps can be added in the same repository.

## Repository layout

- `src/` - Nim source files (`*.nim`)
- `tests/` - Nim unit tests
- `debian/` - Debian packaging metadata
- `po/` - gettext message catalogs
- `docs/` - AsciiDoc man page sources (`docs/*.adoc`)
- `meson.build` - build, test, install, and helper targets

## Example app: `some_puff1`

`some_puff1` is a cat-like utility:

```bash
some_puff1 [OPTION]... [FILE]...
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
sudo apt install meson ninja-build nim gettext asciidoctor
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

Meson runs a Nim unit test from `tests/test_commons.nim` with `nim r`.

## i18n (gettext)

`some_puff1` uses gettext translations under `po/` (`*.po` + generated `.mo` files).

### Sync translation catalogs

```bash
ninja -C /build posync
```

## Install

```bash
meson install -C /build
```

## Debian package

```bash
dpkg-buildpackage -us -uc
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**.  
See `LICENSE` for the full text and supplemental project terms.
