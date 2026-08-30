# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext .po catalog read/write helpers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Literal

from ..l10n import (
    fallback_chain,
    normalize_locale,
    resolve_present_locale,
)

MatchField = Literal["msgid", "both"]


def compile_match_pattern(src: str, *, case_sensitive: bool) -> re.Pattern[str]:
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(src, flags)


def text_matches(pattern: re.Pattern[str], text: str, *, entire: bool) -> bool:
    if not text:
        return False
    if entire:
        return pattern.fullmatch(text) is not None
    return pattern.search(text) is not None


def parse_linguas(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def implemented_locales(root: Path) -> list[str]:
    """Locales with po/<name>.po present (listed in LINGUAS when that file exists)."""
    po_dir = root / "po"
    if not po_dir.is_dir():
        return []
    linguas_path = po_dir / "LINGUAS"
    listed = set(parse_linguas(linguas_path)) if linguas_path.is_file() else set()
    out: list[str] = []
    for po in sorted(po_dir.glob("*.po")):
        loc = po.stem
        if not listed or loc in listed:
            out.append(loc)
    return out


def _unescape_po(s: str) -> str:
    return s.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")


def _escape_po(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_po_string(prefix: str, text: str) -> str:
    if "\n" not in text and '"' not in text and "\\" not in text:
        return f'{prefix}"{_escape_po(text)}"'
    chunks = text.split("\n")
    lines = [f'{prefix}""']
    for i, chunk in enumerate(chunks):
        suffix = "\\n" if i < len(chunks) - 1 else ""
        lines.append(f'"{_escape_po(chunk)}{suffix}"')
    return "\n".join(lines)


def _read_po_field(lines: list[str], idx: int, prefix: str) -> tuple[str, int]:
    line = lines[idx]
    if not line.startswith(prefix):
        return "", idx
    rest = line[len(prefix) :].strip()
    if rest.startswith('"'):
        parts = [_unescape_po(rest.strip('"'))]
        idx += 1
        while idx < len(lines) and lines[idx].startswith('"'):
            parts.append(_unescape_po(lines[idx].strip().strip('"')))
            idx += 1
        return "".join(parts), idx
    return "", idx + 1


def parse_po_entries(body: str) -> list[tuple[str, str]]:
    lines = body.splitlines()
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("msgid "):
            mid, i = _read_po_field(lines, i, "msgid ")
            if i < len(lines) and lines[i].startswith("msgstr "):
                ms, i = _read_po_field(lines, i, "msgstr ")
                if mid:
                    entries.append((mid, ms))
                continue
        i += 1
    return entries


def iter_catalog_entries(body: str) -> list[tuple[str, str]]:
    """Return (msgid, msgstr) pairs from a PO catalog body."""
    return parse_po_entries(body)


def list_msgids(root: Path) -> list[str]:
    pot = root / "po" / "zfr.pot"
    if not pot.is_file():
        return []
    body = pot.read_text(encoding="utf-8", errors="replace")
    return [mid for mid, _ms in iter_catalog_entries(body) if mid]


def list_matching_msgids(
    root: Path,
    pattern: re.Pattern[str],
    *,
    entire: bool = False,
) -> list[str]:
    return [mid for mid in list_msgids(root) if text_matches(pattern, mid, entire=entire)]


def catalog_matches(
    root: Path,
    pattern: re.Pattern[str],
    *,
    lang: str | None = None,
    field: MatchField = "msgid",
    entire: bool = False,
) -> list[tuple[str, str, str]]:
    """Return (locale, msgid, msgstr) rows where *pattern* matches selected fields."""
    rows: list[tuple[str, str, str]] = []
    locales = [normalize_locale(lang)] if lang else implemented_locales(root)
    seen: set[tuple[str, str]] = set()
    for loc in locales:
        found = resolve_po_path(root, loc)
        if found is None:
            continue
        po_path, _resolved = found
        for mid, ms in iter_catalog_entries(
            po_path.read_text(encoding="utf-8", errors="replace")
        ):
            if field == "msgid":
                if not text_matches(pattern, mid, entire=entire):
                    continue
            elif not text_matches(pattern, mid, entire=entire) and not text_matches(
                pattern, ms, entire=entire
            ):
                continue
            key = (loc, mid)
            if key in seen:
                continue
            seen.add(key)
            rows.append((loc, mid, ms))
    return rows


def group_catalog_rows(
    rows: list[tuple[str, str, str]],
    *,
    msgid_order: list[str] | None = None,
) -> list[tuple[str, list[tuple[str, str]]]]:
    """Group (locale, msgid, msgstr) rows by msgid."""
    by_mid: dict[str, list[tuple[str, str]]] = {}
    order: list[str] = []
    for loc, mid, ms in rows:
        if mid not in by_mid:
            by_mid[mid] = []
            order.append(mid)
        by_mid[mid].append((loc, ms))
    if msgid_order is not None:
        rank = {mid: index for index, mid in enumerate(msgid_order)}
        order = sorted(order, key=lambda mid: rank.get(mid, len(rank)))
    return [(mid, by_mid[mid]) for mid in order]


def match_catalog(
    root: Path,
    pattern: re.Pattern[str],
    *,
    lang: str | None = None,
    keys_only: bool = False,
) -> list[tuple[str, str, str | None]]:
    """Return (locale, msgid, msgstr|None) rows matching *pattern* in msgid or msgstr."""
    if keys_only:
        return [("", mid, None) for mid in list_matching_msgids(root, pattern)]
    rows = catalog_matches(root, pattern, lang=lang, field="both")
    return [(loc, mid, ms) for loc, mid, ms in rows]


def get_msgstr(body: str, msgid: str) -> str | None:
    for mid, ms in parse_po_entries(body):
        if mid == msgid:
            return ms or None
    return None


def set_msgstr(body: str, msgid: str, msgstr: str) -> str:
    lines = body.splitlines()
    out: list[str] = []
    i = 0
    replaced = False
    while i < len(lines):
        if lines[i].startswith("msgid "):
            start = i
            mid, next_i = _read_po_field(lines, i, "msgid ")
            if mid == msgid and next_i < len(lines) and lines[next_i].startswith("msgstr "):
                out.extend(lines[start:next_i])
                out.append(_format_po_string("msgstr ", msgstr))
                _ms, i = _read_po_field(lines, next_i, "msgstr ")
                replaced = True
                continue
        out.append(lines[i])
        i += 1
    if not replaced:
        out.extend(
            [
                "",
                _format_po_string("msgid ", msgid),
                _format_po_string("msgstr ", msgstr),
            ]
        )
    text = "\n".join(out)
    if body.endswith("\n"):
        text += "\n"
    return text


def po_stats(po_path: Path) -> dict[str, int]:
    entries = parse_po_entries(po_path.read_text(encoding="utf-8", errors="replace"))
    total = len(entries)
    translated = sum(1 for _mid, ms in entries if ms)
    return {"total": total, "translated": translated, "missing": total - translated}


def resolve_po_path(root: Path, lang: str) -> tuple[Path, str] | None:
    loc = normalize_locale(lang)
    present = set(parse_linguas(root / "po" / "LINGUAS"))
    resolved = resolve_present_locale(loc, present) or loc
    po_path = root / "po" / f"{resolved}.po"
    if po_path.is_file():
        return po_path, resolved
    for fb in fallback_chain(loc):
        fb_res = resolve_present_locale(fb, present) or fb
        candidate = root / "po" / f"{fb_res}.po"
        if candidate.is_file():
            return candidate, fb_res
    return None


def lookup_translation(root: Path, lang: str, msgid: str) -> str | None:
    found = resolve_po_path(root, lang)
    if found is None:
        return None
    po_path, _ = found
    return get_msgstr(po_path.read_text(encoding="utf-8", errors="replace"), msgid)


def update_translation(root: Path, lang: str, msgid: str, msgstr: str) -> Path | None:
    loc = normalize_locale(lang)
    present = set(parse_linguas(root / "po" / "LINGUAS"))
    resolved = resolve_present_locale(loc, present) or loc
    po_path = root / "po" / f"{resolved}.po"
    if not po_path.is_file():
        return None
    body = po_path.read_text(encoding="utf-8", errors="replace")
    po_path.write_text(set_msgstr(body, msgid, msgstr), encoding="utf-8")
    return po_path


def insert_locale(root: Path, lang: str) -> list[str]:
    loc = normalize_locale(lang)
    po_dir = root / "po"
    if not po_dir.is_dir():
        raise FileNotFoundError("po/ directory not found")
    changed: list[str] = []
    linguas_path = po_dir / "LINGUAS"
    present = parse_linguas(linguas_path)
    if loc not in present:
        linguas_path.parent.mkdir(parents=True, exist_ok=True)
        with linguas_path.open("a", encoding="utf-8") as fh:
            if present and not linguas_path.read_text(encoding="utf-8").endswith("\n"):
                fh.write("\n")
            fh.write(f"{loc}\n")
        changed.append(str(linguas_path.relative_to(root)))
    po_path = po_dir / f"{loc}.po"
    if not po_path.is_file():
        pots = sorted(po_dir.glob("*.pot"))
        if not pots:
            raise FileNotFoundError("no .pot template in po/")
        subprocess.run(
            [
                "msginit",
                "-i",
                str(pots[0]),
                "-o",
                str(po_path),
                "-l",
                loc,
                "--no-translator",
            ],
            check=True,
            capture_output=True,
        )
        changed.append(str(po_path.relative_to(root)))
    return changed


def delete_locale(root: Path, lang: str) -> list[str]:
    loc = normalize_locale(lang)
    removed: list[str] = []
    linguas_path = root / "po" / "LINGUAS"
    if linguas_path.is_file():
        lines = [
            ln
            for ln in linguas_path.read_text(encoding="utf-8").splitlines()
            if ln.split("#", 1)[0].strip() != loc
        ]
        linguas_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        removed.append(str(linguas_path.relative_to(root)))
    po_path = root / "po" / f"{loc}.po"
    if po_path.is_file():
        po_path.unlink()
        removed.append(str(po_path.relative_to(root)))
    docs_loc = root / "docs" / loc
    if docs_loc.is_dir():
        for p in sorted(docs_loc.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                p.rmdir()
        docs_loc.rmdir()
        removed.append(str(docs_loc.relative_to(root)))
    return removed
