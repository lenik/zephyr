# Agent notes

See `.cursor/rules/version-changelog.mdc` for the changelog / release-tag
workflow. `VERSION` is maintained by the git pre-commit hook from
`debian/changelog`; do not edit it by hand.

After a solidified `v*` tag, open the next changelog stanza inside the normal
feature commit(s)—do not make a separate “open version” commit. Only an
explicit user-requested release uses a release commit (and tag).
