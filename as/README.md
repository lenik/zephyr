THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is a minimal **NASM x86-64 Linux** template built with Meson.
`some_puff1` copies stdin to stdout using raw syscalls (similar to `cat`).

## Repository layout

- `src/some_puff1.asm` - main program
- `src/commons.inc` - shared constants (buffer size, syscall numbers)
- `tests/smoke.sh` - stdin/stdout smoke test
- `meson.build` - `nasm -f elf64` and `ld` link

## Example app: `some_puff1`

```bash
some_puff1 < file
echo hello | some_puff1
```

## Build

```bash
sudo apt install meson ninja-build nasm asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**. See `LICENSE`.
