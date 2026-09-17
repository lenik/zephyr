# Parallel building and packaging jobs

`zfr build`, `zfr package`, and `zfr release` all accept `-j` / `--job N`, but
**jobs** means different things at different layers. This note describes the
full multi-job pipeline: what runs in parallel, what stays sequential, how
Debian’s `-j` auto mode works, and how build logs are captured.

## Two different axes

Zephyr packaging is intentionally **not** “run every packager at once.”

| Axis | What it controls | Default |
| --- | --- | --- |
| **Packager pipeline** | Order of packaging *kinds* (`deb`, then `rpm`, then `mingw`, …) | Always **sequential** |
| **`-j` / `--job`** | Parallelism *inside* one packager’s build (debuild, make, meson, …) | **auto** |

So when you see:

```text
zfr package: detected deb(debian/control), rpm(packaging/rpm); …
; sequential (jobs=auto per packager)
```

that means:

1. Detected kinds will run **one after another** (deb finishes before rpm
   starts).
2. Each kind’s *internal* build may use multiple CPU cores via `-j`.

This split exists so packagers do not fight over shared output directories,
upload slots, or interactive error browsing, while still letting a single
Debian or RPM build use the machine fully.

## What “auto” means for `-j`

### CLI default

`-j` / `--job` defaults to **unset** (`None`). That is the auto mode:

- **debuild / dpkg-buildpackage**: argv gets a bare `-j` **with no number**.
  dpkg then chooses parallelism (its own auto / processor count policy).
  `zfr` does **not** pin `DEB_BUILD_OPTIONS=parallel=N` in this mode; the bare
  `-j` is allowed to own that decision.
- **make / Meson / CMake / Cargo / Go** (and other tools that need a concrete
  integer): `zfr` resolves auto to `os.cpu_count()` (at least 1) and passes
  `-jN`, `--parallel N`, or the equivalent.

Explicit `-j 4` (or any positive `N`) is a **total job budget**. When the
package *plan* runs workers concurrently, `split_job_budget(N, K)` divides
`N` across those `K` workers. Today's packager pipeline is **sequential**
(`K=1`), so each packager receives the full `N` (debuild `-j4`,
`DEB_BUILD_OPTIONS=parallel=4`, make `-j4`, …). Bare `-j` / omitted `-j`
stays auto for every worker.

### Why bare `-j` for Debian

Older `zfr package` behaviour expanded the default to `-j$(nproc)` and always
wrote a numeric `parallel=N`. That forced a count even when the packager or
`debian/rules` already had a better policy. The default is now:

```text
+ debuild -j
```

not:

```text
+ debuild -j16
```

Unless you asked for sixteen jobs.

## End-to-end: `zfr package`

1. **Detect** packaging kinds under the project (`debian/control` → deb,
   `packaging/rpm` → rpm, npm/vsix, mingw Makefiles, …).
2. **Filter** with `--only`, `--no-deb`, `--no-rpm`, and each packager’s
   `skip_reason` (missing tools, missing `.build-host`, …). Skipped kinds are
   recorded but do not start a build.
3. **Dry-run** (`--dry-run`) prints the planned commands and exits without
   requiring `fdmux`.
4. **Real run** (TTY):
   - Requires **`fdmux`** on `PATH`.
   - Opens a live **status board** (one line per packager: pending → running →
     ok/fail, with a tip from the latest log line).
   - For each **active** kind, in order:
     - Create `~/.cache/zfr/last-package.d/<kind>.fdm`.
     - Wrap stdout/stderr through FDM capture while the packager builds.
     - Mark ok/fail on the board.
5. **Persist** `~/.cache/zfr/last-package.json` plus the `.fdm` files for
   `zfr lasterror`.
6. **Upload** (default on; `-U` / `--no-upload` skips): dput / registry /
   packaging outs after a successful build.

Failures open an interactive browser when stdin/stdout are TTYs; otherwise the
process exits non-zero and you inspect with `zfr lasterror`.

## Packagers and how they use jobs

### Debian (`DebPackager`)

Local path:

- Merge environment; if jobs are numeric, set
  `DEB_BUILD_OPTIONS=… parallel=N`.
- Prefer `debuild`, else `dpkg-buildpackage`.
- Append `debuild_jobs_args(jobs)` → `["-j"]` or `["-jN"]`.

Docker / remote (`-d`, `-s`): the same job policy is embedded in the
`debian_build_inner` shell script run under `build4`.

### Make-based kinds (rpm, mingw, …)

`MakeTargetPackager` always calls `resolve_jobs()` so make receives a concrete
`-jN` (CPU count when auto).

### Compile-only (`zfr build`)

`zfr build` always needs a number for Meson/CMake/make/cargo. Auto resolves to
CPU cores before the build system is invoked. Packaging later in `zfr release`
still keeps Debian auto as bare `-j` unless you passed `-j N` on the release
command line.

## `zfr release` interaction

Release’s build step:

1. Compiles with `build_project(..., jobs=resolve_jobs(opts.jobs))` — numeric.
2. Packages with `package_project(..., jobs=opts.jobs)` — **preserves auto** for
   debuild.

So `zfr release` with no `-j` still gets a parallel compile and an
auto-parallel Debian package build, without forcing the same integer into both
layers.

## FDM capture (why jobs ≠ log spaghetti)

Each packager’s stdout and stderr are encoded as **FDM text runs** (channel 1 =
out, channel 2 = err) into a per-kind `.fdm` file. The status board polls the
capture for a short “tip” line so a long `debuild` does not flood the terminal.
After the run:

- `zfr lasterror` demuxes or pages those files.
- The last-run JSON points at the same cache directory so a later shell can
  inspect a failed rpmbuild without scrolling away the success of deb.

Parallelism *inside* one packager still produces one FDM stream for that kind;
parallelism *across* packagers is avoided so those streams stay attributable.

## Practical recipes

```bash
# Default: sequential packagers, auto jobs inside each (debuild -j)
zfr package

# Pin eight jobs for every packager that honors -j
# (sequential plan ⇒ each gets the full budget of 8)
zfr package -j 8

# Bare -j is the same as omitting it (auto / debuild -j)
zfr package -j

# Only Debian, unsigned, no upload, see the planned -j
zfr package --only deb --unsigned -U --dry-run

# Release: numeric compile jobs + auto debuild unless -j given
zfr release -l --unsigned
zfr release -l --unsigned -j 4
```

## Summary

- **Pipeline**: packagers run **sequentially**.
- **`-j`**: per-packager build parallelism, default **auto**.
- **Debian auto**: bare `debuild -j` (no number); do not confuse with “run
  deb and rpm at the same time.”
- **Logs**: one FDM file per packager; live tips on a TTY; `zfr lasterror` for
  post-mortem.

See also `zfr package --help`, `zfr build --help`, and `man zfr`.
