# Windows packaging (stub)

Build with Meson + Ninja on Windows (MSYS2/MinGW or native MSVC toolchain).

```sh
meson setup build --prefix=C:/opt/zephyr
meson compile -C build
meson install -C build --destdir=stage
```

Version: `zfr version` from the project root.

TODO: WiX/NSIS installer; zip portable layout under `stage/`.
