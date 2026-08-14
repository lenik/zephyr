THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is a Meson-based **shared/static C++ library** template (`cpplib`) with an example CLI app.
It builds `libzephyr` (shared + static), installs headers/pkg-config, and ships `some_puff1` as a sample consumer; more apps can be added in the same repository.

## Repository layout

- `src/` - source code for apps and shared pieces
- `tests/` - unit tests (`*_unit.cpp` / `*_test.cpp`) using the Check framework
- `debian/` - Debian packaging metadata
- `docs/` - AsciiDoc man page sources (`docs/*.adoc`)
- `meson.build` - top-level build definition and helper targets

## Example app: `some_puff1`

`some_puff1` is a cat-like utility:

```bash
some_puff1 [OPTION]... [FILE]...
```

- If no `FILE` is provided, it reads from `stdin`.
- If a `FILE` is `-`, it reads from `stdin` at that position.
- Output is written to `stdout`.

Supported options:

- `-v`, `--verbose`
- `-q`, `--quiet`
- `-h`, `--help`
- `--version`

## Build and test

### Build dependencies

```bash
sudo apt install meson ninja-build g++ pkg-config check libbas-cpp-dev asciidoctor
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
```

Unit tests are auto-discovered from `tests/*_test.cpp` / `tests/*_unit.cpp` and registered in Meson.

## i18n (gettext)

`some_puff1` uses gettext translations under `po/` (`*.po` + generated `.mo` files).

- Installed runtime loads translations from system locale dir.
- Dev runtime (`/build/some_puff1`) prefers project-local translations from `/build/po` if present.

### Sync translation catalogs

Use `posync` to update catalogs from current source strings:

```bash
ninja -C /build posync
```

### Build translation files

```bash
ninja -C /build
```

### Quick locale testing

```bash
LANGUAGE=ja /build/some_puff1 -h
LANGUAGE=zh_CN /build/some_puff1 -h
```

## Install / symlink helpers

```bash
meson install -C /build
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
