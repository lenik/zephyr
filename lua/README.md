# zephyr

`zephyr` is a **Lua** + Meson project template for small command-line apps.
`some_puff1` is one **example app** in this template; more apps can be added in the same repository.

## Repository layout

- `src/` - Lua sources (`some_puff1.lua` example app and `commons.lua` shared helpers)
- `tests/` - Lua unit tests (`lua tests/test_commons.lua`)
- `docs/` - AsciiDoc man page sources (`docs/*.adoc`)
- `meson.build` - install rules, tests, and helper targets

## Example app: `some_puff1`

`some_puff1` is a cat-like utility:

```bash
some_puff1 [OPTION]... [FILE]...
```

Supported options: `-v`, `--verbose`; `-q`, `--quiet`; `-h`, `--help`; `--version`.

## Build and test

### Build dependencies (Debian example)

```bash
sudo apt install meson ninja-build lua5.4 luajit asciidoctor
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
# or directly:
LUA_PATH=src/?.lua lua tests/test_commons.lua
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**. See `LICENSE` for the full text.
