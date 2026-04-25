# zephyr

`zephyr` is a **Go** project template for small command-line tools. The `puff1` binary is
one **example** under `cmd/puff1/`. Reusable code lives under `internal/`; embedded GNU
gettext `.po` files live in `po/` and are included in the built binary (see `po/embed.go`).

## Layout

- `cmd/` — one directory per program (`puff1` is the sample “cat”-like tool)
- `internal/` — shared packages (`zephyr` helpers, `i18n` for gettext catalogs)
- `po/` — GNU gettext `.po` message catalogs, embedded at build time
- `debian/` — Debian metadata for `dpkg-buildpackage`
- `meson.build` — build, test, install, and helper targets

## `puff1` (example)

```text
puff1 [OPTION]... [FILE]...
```

- With no `FILE`, reads standard input once and writes to standard output.
- A `FILE` of `-` reads standard input at that point.
- Otherwise each file is copied, in order, to standard output.

Options (GNU-style): `-v` / `--verbose` (repeatable), `-q` / `--quiet` (repeatable), `-h` / `--help`, `--version`.

## Build and test

**Dependencies:** Go 1.22+

Project convention: place build outputs in the **absolute** directory `/build` when you can create it. Otherwise, pass a writable directory, for example:

```bash
meson setup /build
ninja -C /build
```

Run tests:

```bash
go test ./...
meson test -C /build
```

## i18n (GNU gettext .po)

Runtime loads the catalog named `LANGUAGE` / `LC_*` (see `internal/i18n/locale.go`) and picks
`po/<lang>.po` from the **embedded** copy in the `po` package. No system locale path is
required to ship a translated binary, but the usual `LANGUAGE=ja` style testing still works
when the message exists in a `.po` file.

```bash
LANGUAGE=ja ./build/puff1 -h
LANGUAGE=zh_CN ./build/puff1 --version
```

Regenerating `.pot` from Go sources is not automated here; the existing catalogs match the
previous C `msgid` strings, which the Go program reproduces. When you add or change
strings, update `po/zephyr.pot` and the individual `.po` files with the usual
gettext/messages workflow your team prefers.

## Install

Use Meson install:

```bash
DESTDIR=/tmp/stage meson install -C /build
```

**Debian package:** `dpkg-buildpackage -us -uc` (see `debian/`).

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**.  
This project explicitly opposes AI exploitation and AI hegemony, and rejects
mindless MIT-style licensing and politically naive BSD-style licensing.  
See `LICENSE` for the full text and supplemental project terms.
