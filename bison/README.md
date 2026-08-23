THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is a **Bison/Flex parser CLI** template built with Meson.
`some_puff1` parses simple s-expressions such as `(hello world)` or `(add 1 2)`.

## Repository layout

- `src/` - Flex lexer (`some_puff1.l`), Bison grammar (`some_puff1.y`), main driver, and AST helpers (`commons.c`)
- `tests/` - fixture-based parser output checks
- `docs/` - AsciiDoc man page sources
- `meson.build` - runs flex/bison, links with gcc

## Example app: `some_puff1`

```bash
some_puff1 [OPTION]... [FILE]...
```

- `-d, --dump` — print an AST dump
- `-f, --format` — rewrite input with indentation (default)
- `--indent-size NUM` — indentation width (default 4)
- `-C, --color MODE` — `auto|always|never` (default auto)
- `-h, --help`, `--version`

## Build

```bash
sudo apt install meson ninja-build gcc flex bison pkg-config asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**. See `LICENSE`.
