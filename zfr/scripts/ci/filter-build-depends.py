#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Drop Build-Depends/Depends packages that apt-cache cannot resolve."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def _filter_field(text: str, field: str) -> str:
    m = re.search(rf"(?ms)^({re.escape(field)}:\s*)(.*?)(?=\n\S|\Z)", text)
    if not m:
        return text
    body = m.group(2)
    parts: list[str] = []
    for raw in re.sub(r"\s*\n\s*", " ", body).split(","):
        raw = raw.strip()
        if not raw:
            continue
        name = re.split(r"[(\s|]", raw, maxsplit=1)[0].strip()
        if not name:
            continue
        if name.startswith("${") or name == "debhelper-compat":
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
            print(f"build-deb: dropping unavailable {field}: {name}", flush=True)
    if field == "Build-Depends" and not parts:
        parts = ["debhelper-compat (= 13)", "meson", "ninja-build", "python3"]
    if field == "Depends" and not parts:
        parts = ["${misc:Depends}"]
    new_body = ", ".join(parts)
    # Preserve multi-line Depends style as a single folded line.
    return text[: m.start(2)] + new_body + text[m.end(2) :]


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "debian/control")
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    text = _filter_field(text, "Build-Depends")
    text = _filter_field(text, "Depends")
    path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
