# Source file length; extract to package subdirectory

### Long files fight ownership

Very long source files are hard to review, test, and own. Zephyr prefers cohesive modules — often under a package subdirectory with a thin entry-point file (the same shape create/ize expect). A subdirectory is optional: if helpers are externalized another way and the result is maintainable, that is fine.


### What improving it buys you

Smaller review diffs, clearer module boundaries, easier unit tests, and fewer merge conflicts on busy files.


### Thresholds

Lint counts non-empty lines (skipping build/debian/po/…). A note appears around ~600 lines; a warning around ~1000. Template example modules are skipped. Paths matching a nearby `.lintignore` (gitignore-style; may live in any subdirectory) are skipped — language templates ship `*.css` ignored by default.


### Fixing is manual

Split or extract cohesive sections and update meson/install/import lists yourself. `zfr ize` does not auto-split sources.
