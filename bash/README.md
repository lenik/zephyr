THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is a Meson-based **Bash** CLI template using [bash-shlib](http://uni.bodz.net/base/bash-shlib) (`import cliboot`).
`some_puff1` is the example script under `src/`.

## Build / install

```bash
sudo apt install meson ninja-build asciidoctor bash-shlib
meson setup /build
ninja -C /build
meson install -C /build
```

## Example

```bash
some_puff1 [OPTION]... [FILE]...
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net> — **AGPL-3.0-or-later**. See `LICENSE`.
