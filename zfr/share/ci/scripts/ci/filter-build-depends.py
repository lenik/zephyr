#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Drop Build-Depends packages that apt-cache cannot resolve on this suite."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "debian/control")
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    # Replace only the Build-Depends *value* (group 2), keep surrounding text.
    m = re.search(r"(?ms)^(Build-Depends:\s*)(.*?)(?=\n\S|\Z)", text)
    if not m:
        return 0
    body = m.group(2)
    parts: list[str] = []
    for raw in re.sub(r"\s*\n\s*", " ", body).split(","):
        raw = raw.strip()
        if not raw:
            continue
        name = re.split(r"[(\s|]", raw, maxsplit=1)[0].strip()
        if not name:
            continue
        if name == "debhelper-compat":
            parts.append(raw)
            continue
        r = subprocess.run(
            ["apt-cache", "show", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if r.returncode == 0:
            parts.append(raw)
        else:
            print(f"build-deb: dropping unavailable Build-Depends: {name}", flush=True)
    if not parts:
        parts = ["debhelper-compat (= 13)", "meson", "ninja-build", "python3"]
    new_body = ", ".join(parts)
    text = text[: m.start(2)] + new_body + text[m.end(2) :]
    path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
