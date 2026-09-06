# SPDX-License-Identifier: AGPL-3.0-or-later
"""Install Cursor agent rules shipped with zfr (create / ize)."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import pkgdatadir

RULE_NAME = "version-changelog.mdc"


def cursor_rule_src(name: str = RULE_NAME) -> Path | None:
    """Canonical Cursor rule file: pkgdatadir, then source-tree fallback."""
    candidates = [pkgdatadir() / "cursor-rules" / name]
    here = Path(__file__).resolve()
    if here.parent.name == "zfr_lib":
        zfr_root = here.parents[2]
        candidates.append(zfr_root / "cursor-rules" / name)
    for path in candidates:
        if path.is_file():
            return path
    return None


def install_cursor_rules(dest: Path) -> Path | None:
    """Install shipped Cursor rules under *dest*/.cursor/rules/.

    Returns the installed rule path, or None if no source rule is available.
    """
    src = cursor_rule_src()
    if src is None:
        return None
    rules_dir = dest / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    dest_rule = rules_dir / RULE_NAME
    shutil.copy2(src, dest_rule)
    return dest_rule
