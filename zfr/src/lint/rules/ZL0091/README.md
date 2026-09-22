# Hardcoded project version in sources (use @VERSION@ / PROJECT_VERSION)

### Version literals drift

A hardcoded release string diverges from debian/changelog and Meson project_version() the moment you bump.


### Single source of truth

Prefer @VERSION@ / PROJECT_VERSION substituted at build time so `--version`, wrappers, and packages stay aligned.


### Risks when converting

C/C++ usually needs config.h; scripts need *.in. Dry-run ize (`-n`) on large trees before writing.
