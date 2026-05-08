# zephyr

`zephyr` is a C# template for small command-line apps, using Meson for build/test/install.
`puff1` is one **example app** in this template; more apps can be added in the same repository.

## Repository layout

- `lib/Zephyr/` - shared class library (`.csproj` + `common_lib.cs`)
- `apps/Puff1/` - example console app (`Puff1.csproj`, `Program.cs`, `Resources/*.resx`)
- `tests/` - C# smoke/unit tests
- `debian/` - Debian packaging metadata
- `scripts/emit-strings-resx.py` - optional helper to rewrite `apps/Puff1/Resources/Strings*.resx` from the tables in the script
- `zephyr.sln` - Visual Studio / `dotnet build` solution (Zephyr lib + Puff1 + tests)
- `meson.build` - build, test, install, and helper targets

## Example app: `puff1`

`puff1` is a cat-like utility:

```bash
puff1 [OPTION]... [FILE]...
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
sudo apt install meson ninja-build dotnet-sdk-8.0
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

Meson runs a C# smoke/unit test from `tests/TestCommonLib.csproj`.

## i18n (.resx)

`puff1` uses embedded `.resx` under `apps/Puff1/Resources/`. Neutral strings live in `Strings.resx`; per-culture overrides use `Strings.<culture>.resx` and ship as satellite assemblies next to the main DLL.

- Selection follows `LC_ALL` / `LC_MESSAGES` / `LANG` (same idea as typical Unix tools). Example: `LANG=de_DE.UTF-8 /build/puff1 -h` or `LANG=zh-CN.UTF-8 /build/puff1 -h`.

### Regenerating `.resx` from the string tables (optional)

If you add keys to `apps/Puff1/Resources/Strings.resx`, mirror them in the emit script and run:

```bash
python3 scripts/emit-strings-resx.py
```

Then build again so satellite assemblies are updated.

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
