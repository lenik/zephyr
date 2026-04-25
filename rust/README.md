THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is a Rust + Meson project template for small command-line applications.
`puff1` is one **example app**; more apps can be added in the same repository.

## Repository layout

- `src/` - Rust code (`zephyr` library crate + `puff1` binary)
- `build-aux/cargo-build.sh` - build hook used by Meson to run `cargo build --release`
- `po/` - gettext message catalogs
- `debian/` - Debian packaging metadata
- `meson.build` - data files, man page, `install-symlinks`, and Meson-registered `cargo test`
- `Cargo.toml` / `Cargo.lock` - the canonical dependency graph and locked dependency versions

## Example app: `puff1`

`puff1` is a cat-like utility:

```bash
puff1 [OPTION]... [FILE]...
```

- If no `FILE` is provided, it reads from `stdin`.
- If a `FILE` is `-`, it reads from `stdin` at that position.
- Output is written to `stdout`.

Supported options:

- `-v`, `--verbose` (repeat for more log detail)
- `-q`, `--quiet` (reduces log output; wins over `-v` for the effective log level)
- `-h`, `--help`
- `--version`

## Build and test

### Build dependencies (Debian example)

```bash
sudo apt install build-essential meson ninja-build pkgconf cargo rustup gettext
```

(For Debian source packages, `debian/control` lists the build dependencies.)

### Configure and build (Cargo)

```bash
cargo build --release
# ./target/release/puff1
```

### Configure and build (Meson)

The project’s convention is to use the **absolute** Meson build directory `/build` when
you have a writable `/` (for local trees, you can use any other directory):

```bash
meson setup /build
ninja -C /build
```

`ninja` runs `build-aux/cargo-build.sh`, which builds with `cargo` into `{{builddir}}/cargo-target`
and copies `puff1` to the build root.

To avoid a misbehaving `sccache` wrapper during builds, the helper script unsets
`RUSTC_WRAPPER` by default. Set `ZEPHYR_CARGO_ENABLE_SCCACHE=1` if you need it.

### Run tests (Cargo or Meson)

```bash
cargo test
# or, after a Meson setup
meson test -C /build
```

`meson test` runs `cargo test` with a separate `target-dir` under the build directory.

## i18n (gettext)

`puff1` uses gettext (GNU, via the `gettext-rs` crate) and translations under `po/`.

- At runtime, `ZEPHYR_LOCALEDIR` overrides the locale base directory. If it is not set, the
  binary also tries `build/po` (for a Meson build tree) or falls back to `/usr/local/share/locale`.
- Installed systems load translations from the system locale path like other gettext apps.
- The **meson** `install-symlinks` target still symlinks the binary, man page, and bash
  completion; it does not install MO files. Use a normal `meson install` (or a distribution
  package) for a full installation including translations.

### Sync translation catalogs

```bash
ninja -C /build posync
```

`posync` will:

- add missing messages into each language from `po/LINGUAS`
- remove obsolete messages no longer used in source

POT file inputs are listed in `po/POTFILES` (`src/lib.rs` and `src/main.rs`).

### Build translation files

```bash
ninja -C /build
```

### Quick locale testing

```bash
LANGUAGE=ja /path/to/puff1 -h
LANGUAGE=zh_CN /path/to/puff1 -h
```

`LANG=<lang>.<encoding>` may depend on whether that locale is generated on your system.

## Install / symlink helpers

Normal install:

```bash
meson install -C /build
```

Debug symlink workflow (under configured prefix):

```bash
ninja -C /build install-symlinks
ninja -C /build uninstall-symlinks
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
