#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply hand-authored README locale translations under lint/ize rules/."""

from __future__ import annotations

import re
import sys
from hashlib import sha1
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _readme_titles_i18n import TITLES  # noqa: E402
from _readme_bodies_i18n import BODIES, IZE_LINE, LOCALES, PLACEHOLDER_BODY  # noqa: E402

RULE_ROOTS = [ROOT / "src" / "lint" / "rules", ROOT / "src" / "ize" / "rules"]
_IZE_RE = re.compile(r"^Ize rule `([^`]+)` \(`([^`]+)`\)\.\s*$")


def _split(en: str) -> tuple[str, str]:
    lines = en.splitlines()
    if lines and lines[0].startswith("# "):
        return lines[0][2:].strip(), "\n".join(lines[1:]).strip("\n")
    return "", en.strip("\n")


def _body_for(rid: str, body: str, loc: str) -> str:
    m = _IZE_RE.match(body.strip())
    if m:
        code, iid = m.group(1), m.group(2)
        return IZE_LINE[loc].format(code=code, id=iid)
    if body.strip() == "### {title}\n\n{detail}" or body.strip() == "### {title}\n\n{detail}\n":
        return PLACEHOLDER_BODY[loc].rstrip("\n")
    h = sha1(body.encode()).hexdigest()[:12]
    if h not in BODIES:
        raise KeyError(f"no body translation for {rid} hash={h}")
    if loc not in BODIES[h]:
        raise KeyError(f"no {loc} for body {h} ({rid})")
    return BODIES[h][loc].rstrip("\n")


def main() -> int:
    written = 0
    skipped = 0
    errors: list[str] = []
    for root in RULE_ROOTS:
        for d in sorted(root.iterdir()):
            if not d.is_dir():
                continue
            rid = d.name
            src = d / "README.md"
            if not src.is_file():
                continue
            en = src.read_text(encoding="utf-8")
            _en_title, body = _split(en)
            if rid not in TITLES:
                errors.append(f"missing TITLES[{rid}]")
                continue
            for loc in LOCALES:
                try:
                    title = TITLES[rid][loc]
                    body_l = _body_for(rid, body, loc)
                except Exception as e:
                    errors.append(f"{rid}/{loc}: {e}")
                    continue
                text = f"# {title}\n\n{body_l}\n"
                dest = d / f"README-{loc}.md"
                if dest.is_file() and dest.read_text(encoding="utf-8") == text:
                    skipped += 1
                    continue
                dest.write_text(text, encoding="utf-8")
                written += 1
    print(f"written={written} skipped={skipped} errors={len(errors)}")
    for e in errors[:30]:
        print("ERR", e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
