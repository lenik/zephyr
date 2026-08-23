# zephyr

`zephyr` is a **Zig** + Meson project template for small command-line apps.
`some_puff1` is one **example app**; shared helpers live in `src/commons.zig`.
`build.zig` is the Zig build manifest (similar to Go's `go.mod`).

## Layout

- `src/` — `main.zig` (example CLI) and `commons.zig` (shared helpers)
- `build.zig` — native Zig build (`zig build`, `zig test`)
- `docs/` — AsciiDoc man page sources
- `meson.build` — wraps `zig build`, install, and tests

## Build and test

```bash
sudo apt install meson ninja-build zig asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
# or directly:
zig build -Doptimize=ReleaseFast
zig test src/commons.zig
```

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**. See `LICENSE`.
