THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is an **ANTLR4 parser CLI** template built with Meson.
`some_puff1` parses simple s-expressions such as `(hello world)` or `(add 1 2)`.

## Repository layout

- `src/SomePuff1.g4` - ANTLR4 grammar (visitor-enabled generation)
- `src/Main.java` - CLI entry point
- `src/commons.java` - AST dump/format helpers
- `tests/` - Java commons tests
- `meson.build` - runs `antlr4 -visitor`, `javac`, and installs a jar launcher

## Example app: `some_puff1`

```bash
some_puff1 [OPTION]... [FILE]...
```

Parser options match the Bison template: `--dump`, `--format`, `--indent-size`, `--color`, `--help`, `--version`.

## Build

```bash
sudo apt install meson ninja-build default-jdk antlr4 libantlr4-runtime-java asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**. See `LICENSE`.
