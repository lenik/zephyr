# zephyr

Multi-language CLI project templates and helper tools.

`zfr` installs language templates under `/usr/share/zephyr/<lang>/` and
ships cmdline tools to create projects and manage example applications
(**puffs**). Instantiated projects should keep using **`zfr`** on PATH
(`zfr version`, `zfr lint`, …). The tool name **`zfr` is not** a
create/rename magic token; the placeholder that *is* rewritten remains
**`zephyr`** (and **`some_puff1`** for sample puffs).

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
| `/usr/bin/zfr` | Main CLI (`create`, `rename`, `add`, `remove`, `about`, `version`, `lint`, `shape`, `dist`, `ize`, `detect`) |
| `/usr/bin/zfr-{create,rename,add,remove,about,version,lint,shape,dist,ize}` | Thin wrappers |
| `man 1 zfr` | Manual page |

Supported languages include: **bash**, **c**, **clib**, **cpp**, **cpplib**, **csharp**, **erlang**,
**go**, **haskell**, **java**, **perl**, **python**, **ruby**, **rust**, **smalltalk**,
**swift**, and **typescript**.

## Quick start

```bash
zfr create -l python myproj
cd myproj
zfr add myapp
```

`create` copies the template into `./myproj/`, renames the project from
`zephyr` to `myproj`, and removes the sample puff `some_puff1` by default.
It also writes `debian/changelog` and an initial git commit/tag using defaults
`-D unstable`, `-1 0.0.1`, `-a 'Lenik (谢继雷)'`, and `-e lenik@bodz.net`
(override with those flags). Pass puff names on the create line to add them
immediately:

```bash
zfr create -l c widgets hello world
```

Then use `zfr add` / `zfr remove` for more puffs (multiple names allowed).
`zfr lint` checks the tree against zephyr packaging style (missing files,
Meson/Debian/RPM mistakes, leftover template tokens, and recommended
gettext locale coverage) and prints fixes; colors on a TTY. `zfr shape`
prints a 0–100 package-shape score (`-b` prints 0/1); in a monorepo it
scores the *packagedir* (e.g. `repo/bash`), not only the git *repodir*.
`zfr dist` builds a source tarball (`meson dist` at the git
root, otherwise this project only) and is what `rpm/Makefile` and
`ninja srcdist` use. `zfr ize` upgrades an existing tree to current
zephyr style (missing debian/rpm files, meson targets, AsciiDoc man
pages, Meson version substitutions).

When a project has `po/`, zephyr style recommends `LINGUAS` include at least
**ar bn de es fr hi id it ja ko pt ru sv ta te th tr ur vi zh_CN zh_TW**
(English source; `zh-cn`→`zh_CN`, `zh-tw`→`zh_TW`). The `zfr` CLI itself
ships gettext catalogs under `tools/po/` (domain `zfr`).


## Tests

The parent tree ships `tests/` (not installed). From the source root:

```bash
meson setup /build
meson test -C /build
```

Meson runs `python3 -m unittest discover` on `tests/test_*.py`. The suite
creates temporary example projects and exercises the CLI (`create`, `add`,
`remove`, `rename`, `about`, `version`, `lint`, `dist`, `ize`, `detect`).
Set `ZFR_PKGDATADIR` to the source root and `PYTHONPATH` to `tools/`
when running the tests without Meson.

## See also

- `man 1 zfr`
- Per-language `README.md` inside each template directory
- Chinese summary: [README-zh.md](README-zh.md)
