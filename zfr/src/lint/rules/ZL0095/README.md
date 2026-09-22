# posync run_target is externalized as scripts/posync.sh

When po/ exists, meson.run_target('posync') must call scripts/posync.sh rather than an inline bash -euc heredoc. Run `zfr ize` to extract.

### Inline posync is unmaintainable

A bash -euc heredoc inside meson.build duplicates across templates and is painful to debug. The contract is `zfr translate --sync` (Python) wired from run_target('posync'), not an inline heredoc.


### Payoff

One command syncs xgettext/msgmerge locally; ninja posync stays short; CI can call `zfr translate --sync` or import `translate.sync`.


### Solve

Ize rewrites run_target('posync') to invoke translate --sync via the project Python entry (import-first inside zfr). Verify POTFILES and language flags afterward.
