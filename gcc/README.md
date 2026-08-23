THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is a **GNU C extensions** CLI template built with Meson.
Like the plain `c/` template, but compiled with `-std=gnu11` and sample GCC features
(`__attribute__`, statement expressions, `typeof`).

## Repository layout

- `src/some_puff1.c` - example cat-like app using GNU C extensions
- `src/commons.c` / `src/commons.h` - shared helpers
- `tests/commons_test.c` - minimal unit tests
- `meson.build` - Meson project with `add_project_arguments('-std=gnu11')`

## Example app: `some_puff1`

```bash
some_puff1 [OPTION]... [FILE]...
```

Supports `-v`/`--verbose`, `-q`/`--quiet`, `-h`/`--help`, `--version`.

## Build

```bash
sudo apt install meson ninja-build gcc pkg-config asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**. See `LICENSE`.
