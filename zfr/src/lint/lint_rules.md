## ZL0001

### Long files fight ownership

Very long source files are hard to review, test, and own. Zephyr prefers cohesive modules under a package subdirectory with a thin entry-point file — the same shape create/ize expect.


### What improving it buys you

Smaller review diffs, clearer module boundaries, easier unit tests, and fewer merge conflicts on busy files.


### Thresholds

Lint counts non-empty lines (skipping build/debian/po/…). A note appears around ~600 lines; a warning around ~1000. Template example modules are skipped.


### Fixing is manual

Split the file and update meson/install/import lists yourself. `zfr ize` does not auto-split sources.


## ZL0090
### Hardcoded /usr breaks prefixes

Absolute FHS paths (/usr/share, /usr/bin, …) fail under DESTDIR, non-standard prefixes, and Meson configure_file staging.


### Preferred shape

Scripts use @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (or equivalent) and are installed from *.in via Meson.


### What Solve does

Ize renames affected scripts to *.in and wires configure_file. Re-check shebangs and any tests that assumed live paths.


## ZL0091
### Version literals drift

A hardcoded release string diverges from debian/changelog and Meson project_version() the moment you bump.


### Single source of truth

Prefer @VERSION@ / PROJECT_VERSION substituted at build time so `--version`, wrappers, and packages stay aligned.


### Risks when converting

C/C++ usually needs config.h; scripts need *.in. Dry-run ize (`-n`) on large trees before writing.


## ZL0094
### Substitution without a consumer is incomplete

Meson must both define VERSION/PROJECT_VERSION and have sources that actually read it — otherwise packaged binaries still lie.


### How it is checked

Looks for configuration_data keys and for @VERSION@ / PROJECT_VERSION usage in installed sources.


### Closing the loop

Add the missing half (subst or consumer). Solve maps to the subst ize steps when available.


## ZL0095
### Inline posync is unmaintainable

A bash -euc heredoc inside meson.build duplicates across templates and is painful to debug. The contract is `zfr translate --sync` (Python) wired from run_target('posync'), not an inline heredoc.


### Payoff

One command syncs xgettext/msgmerge locally; ninja posync stays short; CI can call `zfr translate --sync` or import `translate.sync`.


### Solve

Ize rewrites run_target('posync') to invoke translate --sync via the project Python entry (import-first inside zfr). Verify POTFILES and language flags afterward.


## ZL0096
### Maintenance scripts belong under scripts/

install-symlinks / deploy helpers at the repo root clutter the packaging surface. Zephyr keeps those under scripts/. Catalog sync and DESTDIR preview are `zfr translate --sync` and `zfr build --look` instead of bespoke posync.sh/look.sh when possible.


### Detection

Flags root *.sh maintenance names and inline run_target bodies that should be externalized or replaced with zfr subcommands.


### After moving

Update docs and any CI that called the old paths. Solve rewrites Meson run_targets to scripts/… or zfr translate/build.


## family:debian

### Debian is the APT contract

control / rules / copyright / source format decide how the package builds and what users install. Zephyr standardizes on Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### This check: {title}

{detail}
      Default severity hint: {sev}.


### Why it matters

Wrong Architecture, missing Build-Depends, or a non-Meson rules file fail debuild or produce unloadable packages even when local compiles succeed.


### When editing packaging

Ize may rewrite from templates — always diff Maintainer, Depends, and Architecture before upload.


## family:rpm

### RPM must mirror Meson/Debian

spec %files, BuildArch, and Version have to describe the same payload Meson installs. Project-local rpmbuild TOPDIR and stale file lists are common failure modes.


### This check: {title}

{detail}
      Severity hint: {sev}.


### Typical fallout

Unpackaged files, wrong noarch/ELF, leftover rpmbuild/, or Debian substvars copied into Requires.


## family:meson

### Meson is the build system of record

Identity, license, version source, man pages, completion, and look/posync targets live in meson.build. Drift here breaks Debian and RPM alike.


### This check: {title}

{detail}


### Editing tips

Ize patches meson.build; reconcile custom targets with template blocks and re-configure after large edits.


## family:i18n

### Locales are a product surface

Gettext catalogs and whole-document man/<locale>/ pages gate what users see at the configured l10n level (`-l` / lint.options).


### This check: {title}

{detail}


### Human work remains

Ize can stub .po files and fix wrap style; real translation and man localization still need people (or `zfr translate`). Long browse essays live in lint_rules-<locale>.xml — hand-translate those; do not wait on slow machine translation.


## family:layout

### Shared layout keeps tools oriented

LICENSE, man/, VERSION, hooks, completion, and scripts/ are the landmarks create/ize/lint/release expect.


### Missing or wrong: {title}

{detail}


### Scaffold refresh

Solve may install or refresh files from the template (.githooks, LICENSE, cursor rules, …). Review before commit.


## family:lang

### Language-template expectations

{title}. Each language keeps idiomatic markers (tests/, Cargo.toml, bas i18n helpers, bash *.in, …) so the tree stays packagable.


### Details

{detail}


## family:identity

### One name across ecosystems

Directory name, meson project(), debian Source, and RPM Name must agree. Mismatches confuse rename, release, and repos.


### Check: {title}

{detail}


## family:source

### Source hygiene

{title}. Covers length and hardcoded paths/versions that break relocatable installs.


### How lint looks

{detail}


## family:tokens

### {title}

{detail}


## family:template

### {title}

{detail}


## family:readme

### {title}

{detail}


## family:generic

### {title}

Rule {id} (`{code}`) is part of the zephyr packaging/
      layout contract. Default severity hint: {sev}.


### What lint does

{detail}
      Implemented under `{code}` in `zfr lint`. Findings carry
      a concrete fix string when possible. Remap severity with
      `-w` / `-e` / `--strict`.


### Changing the tree

Fixes may touch packaging, meson.build, sources, or scaffold
      copies. Diff Maintainer, Depends, %files, and *.in scripts
      before upload.


## ize

### Solve / ize

Clicking Solve runs only: {targets}.
      Equivalent CLI: `{cmd}`
      Use `-n` for a dry plan. Output is captured with fdmux
      (ordered stdout/stderr).


### No Solve mapping {none}

This finding has no `zfr ize --only …` shortcut. Follow the
      fix text (or a broader `zfr ize` if several related gaps
      exist), then re-lint.
