# zephyr

`zephyr` is a **Pascal (Free Pascal)** + Meson project template for small CLI apps.

## Build dependencies (Debian)

```bash
sudo apt install meson ninja-build fpc asciidoctor
```

## Build

```bash
meson setup /build
ninja -C /build
meson test -C /build
```

## License

AGPL-3.0-or-later — see `LICENSE`.
