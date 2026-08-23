# zephyr

`zephyr` is a **Kotlin** + Meson project template for small command-line apps.
`some_puff1` is one **example app** in this template.

## Repository layout

- `src/` - Kotlin sources (`Main.kt` entry point and `commons.kt` shared helpers)
- `tests/` - Kotlin unit/smoke tests (`TestCommons.kt`)
- `build.gradle.kts` - optional Gradle marker for tooling detection (Meson is canonical)
- `docs/` - AsciiDoc man page sources
- `meson.build` - build, test, install, and helper targets

## Build and test

```bash
sudo apt install meson ninja-build kotlin default-jdk asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

Meson compiles with `kotlinc -include-runtime`, installs `some_puff1.jar`, and provides a
`some_puff1` wrapper script that runs `java -jar`.

## License

Copyright (C) 2026 Lenik <zephyr@bodz.net>

Licensed under **AGPL-3.0-or-later**. See `LICENSE`.
