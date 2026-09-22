#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rewrite runtime PEP604 unions that break on Python 3.9 (EL8/EL9)."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def patch_cli(path: Path) -> bool:
    t = path.read_text(encoding="utf-8")
    if "Callable[[argparse.Namespace], int | None]" not in t:
        return False
    t2 = t
    m = re.search(r"from typing import ([^\n]+)", t2)
    if m and "Optional" not in m.group(1):
        names = [x.strip() for x in m.group(1).split(",") if x.strip()]
        if "Optional" not in names:
            names.append("Optional")
        t2 = t2[: m.start(1)] + ", ".join(names) + t2[m.end(1) :]
    t2 = t2.replace(
        "Callable[[argparse.Namespace], int | None]",
        "Callable[[argparse.Namespace], Optional[int]]",
    )
    if t2 == t:
        return False
    path.write_text(t2, encoding="utf-8")
    return True


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    cli = root / "src" / "cli.py"
    if cli.is_file() and patch_cli(cli):
        print(f"build-rpm: patched {cli} for Python 3.9", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
