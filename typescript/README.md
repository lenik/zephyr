THIS FILE IS GENERATED FROM A TEMPLATE.
Except for the project and program names, all content is placeholder text.
Please rewrite this file to reflect the specific details of the current project.

# zephyr

`zephyr` is a TypeScript CLI project template with Meson for build/test/install
and dual packaging for **pnpm/npm** and **Debian**.
`some_puff1` is one **example app** in this template; more apps can be added in the same repository.

## Repository layout

- `src/` - TypeScript sources (`*.ts`) and the `some_puff1` launcher template
- `tests/` - unit tests using Node's built-in test runner
- `docs/` - AsciiDoctor sources for man and info pages
- `scripts/build-docs.sh` - Asciidoctor → man(1) + info
- `dist/` - `tsc` output (generated; published by the package registry)
- `debian/` - Debian packaging metadata
- `po/` - gettext translation catalogs
- `package.json` / `tsconfig.json` - package and TypeScript configuration
- `meson.build` - Meson build, test, install, and helper targets

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

## pnpm workflow (preferred)

```bash
pnpm install
pnpm run build
pnpm test
pnpm pack   # or: pnpm publish
```

`npm` still works if you prefer it. Runtime depends only on Node.js (no registry
runtime dependencies). `typescript` and `@types/node` are development dependencies used to compile
`src/` into `dist/`. Runtime gettext uses **`node-gettext`** and
**`gettext-parser`** (declared in `package.json` `dependencies`).

## Man and info pages

Documentation is authored in AsciiDoctor ([`docs/some_puff1.adoc`](docs/some_puff1.adoc)):

- man page: `asciidoctor -b manpage`
- info page: AsciiDoctor HTML → Pandoc Texinfo → `makeinfo`

```bash
pnpm run docs
# or via Meson:
ninja -C /build
man /build/some_puff1.1
info -f /build/some_puff1.info
```

## Meson build and test

### Build dependencies

```bash
sudo apt install meson ninja-build nodejs node-typescript gettext \
  asciidoctor pandoc texinfo
```

After `pnpm install`, Meson prefers the local `tsc` under `node_modules/.bin`.

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

Meson compiles with `tsc` and runs `node --test` on the emitted test files.

## i18n (gettext)

`some_puff1` uses gettext translations under `po/` (`*.po` + generated `.mo` files).

Zephyr style recommends `po/LINGUAS` cover at least: **ar bn de es fr hi id it
ja ko pt ru sv ta te th tr ur vi zh_CN zh_TW** (English is the msgid source;
`zh-cn`/`zh-tw` map to `zh_CN`/`zh_TW`).

- Installed runtime loads translations from system locale dir.
- Dev runtime (`/build/some_puff1`) prefers project-local translations from `/build/po` if present.

### Sync translation catalogs

Use `posync` to update catalogs from current source strings:

```bash
ninja -C /build posync
```

`posync` will:

- add missing messages into each language from `po/LINGUAS`
- remove obsolete messages no longer used in source

### Build translation files

```bash
ninja -C /build
```

### Quick locale testing

Prefer `LANGUAGE=<lang>` for predictable gettext selection in dev shells:

```bash
LANGUAGE=ja /build/some_puff1 -h
LANGUAGE=zh_CN /build/some_puff1 -h
```

`LANG=<lang>.<encoding>` may depend on whether that locale is generated on your system.

## Install / symlink helpers

Normal install:

```bash
meson install -C /build
```

Installed layout:

- `$prefix/bin/some_puff1` — launcher
- `$prefix/share/zephyr/*.js` — compiled JavaScript modules
- `$prefix/share/man/man1/some_puff1.1` — man page
- `$prefix/share/info/some_puff1.info` — info manual

Debug symlink workflow (under configured prefix):

```bash
ninja -C /build install-symlinks
ninja -C /build uninstall-symlinks
```

## Debian package

```bash
dpkg-buildpackage -us -uc
```

Debian builds with system `nodejs`, `node-typescript`, and Asciidoctor tooling
(no network `pnpm install` / `npm ci`).

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**.  
This project explicitly opposes AI exploitation and AI hegemony, and rejects
mindless MIT-style licensing and politically naive BSD-style licensing.  
See `LICENSE` for the full text and supplemental project terms.
