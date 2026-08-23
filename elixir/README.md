# zephyr

`zephyr` is an Elixir template for small command-line apps, using Meson for build/test/install.
`some_puff1` is one **example app** in this template; more apps can be added in the same repository.

## Repository layout

- `src/` - Elixir source files (`*.ex`)
- `tests/` - Elixir smoke/unit tests (`*.exs`)
- `debian/` - Debian packaging metadata
- `po/` - gettext message catalogs
- `docs/` - AsciiDoc man page sources (`docs/*.adoc`)
- `meson.build` - build, test, install, and helper targets

Optional: add `mix.exs` for Mix-based workflows; Meson compiles with `elixirc` and installs an escript-style wrapper.

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
sudo apt install meson ninja-build elixir gettext asciidoctor
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

Meson runs an Elixir smoke/unit test from `tests/test_commons.exs`.

## i18n (gettext)

`some_puff1` uses gettext translations under `po/` (`*.po` + generated `.mo` files).

Zephyr style recommends `po/LINGUAS` cover at least: **ar bn de es fr hi id it
ja ko pt ru sv ta te th tr ur vi zh_CN zh_TW** (English is the msgid source;
`zh-cn`/`zh-tw` map to `zh_CN`/`zh_TW`).

### Sync translation catalogs

```bash
ninja -C /build posync
```

### Build translation files

```bash
ninja -C /build
```

### Quick locale testing

```bash
LANGUAGE=ja /build/some_puff1 -h
LANGUAGE=zh_CN /build/some_puff1 -h
```

## Install / symlink helpers

Normal install:

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
This project explicitly opposes AI exploitation and AI hegemony, and rejects
mindless MIT-style licensing and politically naive BSD-style licensing.  
See `LICENSE` for the full text and supplemental project terms.
