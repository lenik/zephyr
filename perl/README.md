THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is a Meson-based **Perl** CLI template. `src/some_puff1.pl` installs as `some_puff1`; helpers live in `src/CommonLib.pm`.

## Build / install

```bash
sudo apt install meson ninja-build perl asciidoctor
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
