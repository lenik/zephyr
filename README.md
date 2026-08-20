# zephyr

Multi-language CLI project templates and helper tools.

`zephyr` installs language templates under `/usr/share/zephyr/<lang>/` and
ships cmdline tools to create projects and manage example applications
(**puffs**).

## Install

### From source (Meson)

```bash
sudo apt install meson ninja-build python3 asciidoctor
meson setup /build
ninja -C /build
sudo ninja -C /build install
```

### Debian package

Build and install from the source tree with the usual `dpkg-buildpackage` /
`debuild` workflow. Runtime needs `python3`; bash completion is recommended.

## Layout

| Path | Purpose |
|------|---------|
| `/usr/share/zephyr/<lang>/` | Language template tree |
| `/usr/bin/zephyr` | Main CLI (`create`, `rename`, `add`, `remove`, `about`, `version`, `lint`, `dist`, `ize`, `detect`) |
| `/usr/bin/zephyr-{create,rename,add,remove,about,version,lint,dist,ize}` | Thin wrappers |
| `man 1 zephyr` | Manual page |

Supported languages include: **bash**, **c**, **clib**, **cpp**, **cpplib**, **csharp**, **erlang**,
**go**, **haskell**, **java**, **perl**, **python**, **ruby**, **rust**, **smalltalk**,
**swift**, and **typescript**.

## Quick start

```bash
zephyr create -l python myproj
cd myproj
zephyr add myapp
```

`create` copies the template into `./myproj/`, renames the project from
`zephyr` to `myproj`, and removes the sample puff `some_puff1` by default.
It also writes `debian/changelog` and an initial git commit/tag using defaults
`-D unstable`, `-1 0.0.1`, `-a 'Lenik (谢继雷)'`, and `-e lenik@bodz.net`
(override with those flags). Pass puff names on the create line to add them
immediately:

```bash
zephyr create -l c widgets hello world
```

Then use `zephyr add` / `zephyr remove` for more puffs (multiple names allowed).
`zephyr lint` checks the tree against zephyr packaging style (missing files,
Meson/Debian/RPM mistakes, leftover template tokens) and prints fixes; colors
on a TTY. `zephyr dist` builds a source tarball (`meson dist` at the git
root, otherwise this project only) and is what `rpm/Makefile` and
`ninja srcdist` use. `zephyr ize` upgrades an existing tree to current
zephyr style (missing debian/rpm files, meson targets, AsciiDoc man
pages, Meson version substitutions).

## Tests

The parent tree ships `tests/` (not installed). From the source root:

```bash
meson setup /build
meson test -C /build
```

Meson runs `python3 -m unittest discover` on `tests/test_*.py`. The suite
creates temporary example projects and exercises the CLI (`create`, `add`,
`remove`, `rename`, `about`, `version`, `lint`, `dist`, `ize`, `detect`).
Set `ZEPHYR_PKGDATADIR` to the source root and `PYTHONPATH` to `tools/`
when running the tests without Meson.

## See also

- `man 1 zephyr`
- Per-language `README.md` inside each template directory
- Chinese summary: [README-zh.md](README-zh.md)
