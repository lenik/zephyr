# macOS packaging (stub)

```sh
meson setup build --prefix=/usr/local
meson compile -C build
DESTDIR=stage meson install -C build
```

Version: `zfr version`.

TODO: `pkgbuild` / `create-dmg` from `stage/usr/local`.
