# Agent notes (zephyr / zfr)

## Version and changelog vs git tags

See also: `.cursor/rules/version-changelog.mdc` (always applied in Cursor).

### Terms

- **Solidified tag**: a version tag that already exists (e.g. `v2.8.9`). That version line is frozen.
- **Open next version**: bump `zfr/VERSION` and prepend a new `zfr/debian/changelog` stanza for the *next* semver. This is **not** a release.
- **Release**: a dedicated commit (message like `Release X.Y.Z: …`) that closes the open stanza; then create tag `vX.Y.Z`.

### Rules

1. **Before the current `VERSION` is tagged**: do **not** bump `VERSION` unless the user explicitly asks for a release/bump. Keep adding bullets under the open changelog stanza.
2. **After that version’s tag exists** (`git rev-parse v$(cat zfr/VERSION)` succeeds): further product changes **must** open the next version automatically — **no extra user command**:
   - Set `zfr/VERSION` to the next patch (or agreed minor/major).
   - Prepend `zephyr (X.Y.Z) …` on `zfr/debian/changelog` with the new work.
   - Commit normally (feature commit or a small “open X.Y.Z” commit). **Do not** title it `Release X.Y.Z` and **do not** tag until a real release is requested.
3. **Release** (user asks to release/tag): finalize the open stanza if needed, commit `Release X.Y.Z: …`, tag `vX.Y.Z`.

### Quick check

```bash
git rev-parse "v$(cat zfr/VERSION)" 2>/dev/null
# success ⇒ that version is solidified → open the *next* version for new work
```

### Anti-patterns

- Bumping past the open version while it is still untagged (unless the user ordered a bump/release).
- Calling a post-tag `VERSION` bump a “Release” or tagging it immediately.
- Editing changelog bullets under a version that already has tag `v*`.
