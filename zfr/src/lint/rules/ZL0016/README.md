# VERSION matches debian/changelog

### Single source of truth

`VERSION` should match the latest `debian/changelog` entry. The standard `.githooks/pre-commit` (with `core.hooksPath=.githooks`) rewrites `VERSION` on commit.


### When a sync hook is configured

If that pre-commit hook is present and syncs VERSION from the changelog, a temporary mismatch is expected until the next commit — lint reports **ok** instead of warning.


### When no hook is configured

A mismatch is a **warn**: align VERSION by hand or install the standard hook via `zfr ize`, then `git config core.hooksPath .githooks`.
