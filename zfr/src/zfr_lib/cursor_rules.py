# SPDX-License-Identifier: AGPL-3.0-or-later
"""Install Cursor agent rules shipped with zfr (create / ize)."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import pkgdatadir

RULE_NAME = "version.mdc"
RULE_NAMES = (RULE_NAME, "translations.mdc", "proxy.mdc")
_OBSOLETE_RULE_NAMES = (
    "version-changelog.mdc",
    "version-control-refactor.mdc",
    "std-files.mdc",
)


def _zfr_source_root() -> Path | None:
    """``zfr/`` directory adjacent to this module when running from a checkout."""
    here = Path(__file__).resolve()
    if here.parent.name != "zfr_lib":
        return None
    # …/zfr/src/zfr_lib/cursor_rules.py → zfr/
    return here.parents[2]


def cursor_rule_src(name: str = RULE_NAME) -> Path | None:
    """Canonical Cursor rule file.

    Prefer the copy shipped next to this ``zfr_lib`` (source tree or
    ``$prefix/share/zephyr/zfr``), then ``pkgdatadir()/cursor-rules/``.
    That way ``zfr ize`` refreshes projects from the rules that match the
    running zfr, not a stale earlier install.
    """
    candidates: list[Path] = []
    zfr_root = _zfr_source_root()
    if zfr_root is not None:
        candidates.append(zfr_root / "cursor-rules" / name)
        # Installed layout: share/zephyr/cursor-rules (sibling of zfr/).
        candidates.append(zfr_root.parent / "cursor-rules" / name)
    candidates.append(pkgdatadir() / "cursor-rules" / name)
    for path in candidates:
        if path.is_file():
            return path
    return None


def install_cursor_rules(dest: Path) -> Path | None:
    """Install shipped Cursor rules under *dest*/.cursor/rules/.

    Always overwrites known rule files so ``zfr ize`` picks up updates.
    Returns the primary rule path, or None if no source rule is available.
    """
    rules_dir = dest / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    for obsolete in _OBSOLETE_RULE_NAMES:
        old = rules_dir / obsolete
        if old.is_file():
            old.unlink()
    primary: Path | None = None
    for name in RULE_NAMES:
        src = cursor_rule_src(name)
        if src is None:
            continue
        dest_rule = rules_dir / name
        shutil.copy2(src, dest_rule)
        if primary is None:
            primary = dest_rule
    return primary
