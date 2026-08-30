# Packaging zephyr

Recipes for releasing the **zephyr** suite: the **zfr** CLI plus language
templates installed under `/usr/share/zephyr/`.

In language *templates*, `zephyr` is also the create/rename magic placeholder.
Here it is the real package name (`zephyr-*.rpm`). Gettext catalogs are
**`zephyr.pot` / `zephyr.mo`**.

Version: `zfr version`.

Local builds: `make -C packaging/<platform>` (or `… local`). `lib/host.sh`
checks whether this host can build a target (`can-local`).

Remote builds (`.config/zephyr/<packaging>.build-host`) are orchestrated by
**gh-makerelease**, not by these Makefiles.

| Platform | Directory | Build |
|----------|-----------|-------|
| RPM      | rpm/      | `make -C packaging/rpm` |
| Win32    | win32/    | `make -C packaging/win32` (innosetup/wix: `build.cmd` / `build.ps1`) |
| macOS    | macos/    | `make -C packaging/macos` |
| Arch     | arch/     | `make -C packaging/arch` |
| FreeBSD  | freebsd/  | `make -C packaging/freebsd` |

Win32 artifacts:

- `win32/mingw/` → `<pkg>_mingw-<ver>.exe`
- `win32/innosetup/` → `<pkg>-<ver>.exe`
- `win32/wix/` → `<pkg>-<ver>.msi`
