# Hardcoded FHS install paths in sources (use @DATADIR@ / configure_file)

### Hardcoded /usr breaks prefixes

Absolute FHS paths (/usr/share, /usr/bin, …) fail under DESTDIR, non-standard prefixes, and Meson configure_file staging.


### Preferred shape

Scripts use @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (or equivalent) and are installed from *.in via Meson.


### What Solve does

Ize renames affected scripts to *.in and wires configure_file. Re-check shebangs and any tests that assumed live paths.
