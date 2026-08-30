# SPDX-License-Identifier: AGPL-3.0-or-later
"""Derive child locale catalogs from parent locales (static tools, no AI)."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from ..l10n import (
    DERIVE_METHOD,
    DERIVE_PARENT,
    LEGACY_LOCALE_ALIASES,
    SOURCE_LOCALE,
    canonical_locale,
    children_of,
    derive_parent,
    normalize_locale,
)

_OPENCC_CONFIG = {
    "opencc_s2t": "s2t.json",
    "opencc_s2tw": "s2tw.json",
    "opencc_s2hk": "s2hk.json",
    "opencc_s2twp": "s2twp.json",
}


def _which_opencc() -> str | None:
    return shutil.which("opencc")


def opencc_convert(text: str, method: str) -> str:
    """Run OpenCC on *text*; return original text when opencc is unavailable."""
    config = _OPENCC_CONFIG.get(method)
    if not config:
        return text
    opencc = _which_opencc()
    if opencc is None:
        return text
    proc = subprocess.run(
        [opencc, "-c", config],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return text
    return proc.stdout


def _parent_po_path(po_dir: Path, parent: str) -> Path | None:
    parent = canonical_locale(parent)
    direct = po_dir / f"{parent}.po"
    if direct.is_file():
        return direct
    for alias, target in LEGACY_LOCALE_ALIASES.items():
        if target == parent:
            candidate = po_dir / f"{alias}.po"
            if candidate.is_file():
                return candidate
    if parent == SOURCE_LOCALE:
        pots = sorted(po_dir.glob("*.pot"))
        if pots:
            return pots[0]
    return None


def _transform_text(text: str, child: str, method: str) -> str:
    if method == "copy":
        return text
    if method.startswith("opencc_"):
        return opencc_convert(text, method)
    return text


def _transform_po_body(body: str, child: str, method: str) -> str:
    if method == "copy":
        out = body
    elif method.startswith("opencc_"):
        # Convert msgstr payloads only; leave msgid (English) untouched.
        def repl(match: re.Match[str]) -> str:
            prefix, payload = match.group(1), match.group(2)
            converted = _transform_text(payload, child, method)
            return prefix + converted

        out = re.sub(
            r'(^msgstr(?:\[\d+\])? )((?:"(?:\\.|[^"\\])*"(?:\n)?)+)',
            repl,
            body,
            flags=re.MULTILINE,
        )
    else:
        out = body
    out = re.sub(
        r'^"Language: [^\\"]*\\n"',
        f'"Language: {child}\\n"',
        out,
        count=1,
        flags=re.MULTILINE,
    )
    if '"Language:' not in out:
        out = out.replace(
            '"Content-Type: text/plain; charset=UTF-8\\n"',
            f'"Content-Type: text/plain; charset=UTF-8\\n"\n"Language: {child}\\n"',
            1,
        )
    return out


def _locale_explicitly_used(child: str, linguas: set[str]) -> bool:
    """True when *child* is listed directly in po/LINGUAS."""
    if not linguas:
        return False
    child = normalize_locale(child)
    for entry in linguas:
        if normalize_locale(entry) == child or entry == child:
            return True
    return False


def derive_po_file(
    po_dir: Path,
    child: str,
    *,
    dry_run: bool = False,
    force: bool = False,
    skip_explicit: bool = False,
    linguas: set[str] | None = None,
) -> Path | None:
    """Create po/<child>.po from its derive parent when missing or *force*."""
    child = normalize_locale(child)
    parent = derive_parent(child)
    if parent is None:
        return None
    if skip_explicit and linguas and _locale_explicitly_used(child, linguas):
        return None
    dest = po_dir / f"{child}.po"
    if dest.is_file() and not force:
        return dest
    src = _parent_po_path(po_dir, parent)
    if src is None:
        return None
    method = DERIVE_METHOD.get(child, "copy")
    body = src.read_text(encoding="utf-8")
    new_body = _transform_po_body(body, child, method)
    if dry_run:
        return dest
    dest.write_text(new_body, encoding="utf-8")
    return dest


def derive_man_file(
    docs_dir: Path,
    stem: str,
    child: str,
    *,
    dry_run: bool = False,
    force: bool = False,
    skip_explicit: bool = False,
    linguas: set[str] | None = None,
) -> Path | None:
    child = normalize_locale(child)
    parent = derive_parent(child)
    if parent is None:
        return None
    if skip_explicit and linguas and _locale_explicitly_used(child, linguas):
        return None
    dest = docs_dir / child / stem
    if dest.is_file() and not force:
        return dest
    src = docs_dir / parent / stem
    if not src.is_file():
        for alias, target in LEGACY_LOCALE_ALIASES.items():
            if target == parent:
                alt = docs_dir / alias / stem
                if alt.is_file():
                    src = alt
                    break
    if not src.is_file():
        return None
    method = DERIVE_METHOD.get(child, "copy")
    body = src.read_text(encoding="utf-8")
    new_body = _transform_text(body, child, method)
    if dry_run:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(new_body, encoding="utf-8")
    return dest


def derive_locales(
    root: Path,
    *,
    locales: tuple[str, ...] | None = None,
    dry_run: bool = False,
    force: bool = False,
    skip_explicit: bool = True,
) -> list[str]:
    """Derive missing child PO + man pages under *root*. Returns paths written."""
    targets = locales or tuple(DERIVE_PARENT)
    po_dir = root / "po"
    docs = root / "docs"
    written: list[str] = []
    linguas: set[str] = set()
    linguas_path = po_dir / "LINGUAS"
    if linguas_path.is_file():
        from ..translate.po_files import parse_linguas

        linguas = set(parse_linguas(linguas_path))
    skip = skip_explicit and not force

    for child in targets:
        child = normalize_locale(child)
        if derive_parent(child) is None:
            continue
        if po_dir.is_dir():
            existed = (po_dir / f"{child}.po").is_file()
            po = derive_po_file(
                po_dir,
                child,
                dry_run=dry_run,
                force=force,
                skip_explicit=skip,
                linguas=linguas,
            )
            if po is not None and not dry_run and po.is_file() and (force or not existed):
                written.append(str(po.relative_to(root)))
        if docs.is_dir():
            for adoc in docs.glob("*.adoc"):
                dest = docs / child / adoc.name
                existed = dest.is_file()
                man = derive_man_file(
                    docs,
                    adoc.name,
                    child,
                    dry_run=dry_run,
                    force=force,
                    skip_explicit=skip,
                    linguas=linguas,
                )
                if man is not None and not dry_run and man.is_file() and (force or not existed):
                    written.append(str(man.relative_to(root)))
    return written


def derive_children_of(
    root: Path,
    parent: str,
    *,
    dry_run: bool = False,
    force: bool = False,
    skip_explicit: bool = True,
) -> list[str]:
    return derive_locales(
        root,
        locales=children_of(parent),
        dry_run=dry_run,
        force=force,
        skip_explicit=skip_explicit,
    )
