# SPDX-License-Identifier: AGPL-3.0-or-later
"""Derive child locale catalogs from parent locales (static tools, no AI)."""

from __future__ import annotations

import os
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

_DERIVED_FROM_RE = re.compile(r"^# Derived-From:.*$", re.MULTILINE)
_DERIVED_METHOD_RE = re.compile(r"^# Derived-Method:.*$", re.MULTILINE)


def default_build_po_dir(root: Path) -> Path:
    """Output directory for derived ``.po`` files (never under the source tree)."""
    meson = os.environ.get("MESON_BUILD_ROOT")
    if meson:
        return Path(meson) / "po"
    return root / "build" / "po"


def default_build_docs_dir(root: Path, po_dir: Path | None = None) -> Path:
    if po_dir is not None:
        return po_dir.parent / "docs"
    meson = os.environ.get("MESON_BUILD_ROOT")
    if meson:
        return Path(meson) / "docs"
    return root / "build" / "docs"


def _which_opencc() -> str | None:
    return shutil.which("opencc")


def _dest_fresh(dest: Path, src: Path) -> bool:
    """True when *dest* exists and is not older than *src* (mtime).

    Equal timestamps count as fresh: GNU gettext *msgfmt* 0.23+ stamps the
    ``.mo`` with the source ``.po`` mtime, which must not trigger a rebuild.
    """
    if not dest.is_file():
        return False
    return dest.stat().st_mtime_ns >= src.stat().st_mtime_ns


def _opencc_config_path(config: str) -> str:
    """Resolve an OpenCC config name to a path *opencc* will accept."""
    candidate = Path(config)
    if candidate.is_file():
        return str(candidate)
    for base in (
        Path("/usr/share/opencc"),
        Path("/usr/local/share/opencc"),
    ):
        path = base / config
        if path.is_file():
            return str(path)
    return config


def opencc_convert(text: str, method: str) -> str:
    """Run OpenCC on *text*; return original text when opencc is unavailable."""
    config = _OPENCC_CONFIG.get(method)
    if not config:
        return text
    opencc = _which_opencc()
    if opencc is None:
        return text
    cfg = _opencc_config_path(config)
    proc = subprocess.run(
        [opencc, "-c", cfg],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return text
    # OpenCC may omit a trailing newline; keep caller text shape otherwise.
    out = proc.stdout
    if text and not text.endswith("\n") and out.endswith("\n"):
        out = out[:-1]
    return out


def _parent_po_path(src_po_dir: Path, build_po_dir: Path, parent: str) -> Path | None:
    parent = canonical_locale(parent)
    for base in (src_po_dir, build_po_dir):
        direct = base / f"{parent}.po"
        if direct.is_file():
            return direct
        for alias, target in LEGACY_LOCALE_ALIASES.items():
            if target == parent:
                candidate = base / f"{alias}.po"
                if candidate.is_file():
                    return candidate
    if parent == SOURCE_LOCALE:
        pots = sorted(src_po_dir.glob("*.pot"))
        if pots:
            return pots[0]
    return None


def _transform_text(text: str, child: str, method: str) -> str:
    if method == "copy":
        return text
    if method.startswith("opencc_"):
        return opencc_convert(text, method)
    return text


def _inject_derived_headers(body: str, parent: str, method: str) -> str:
    body = _DERIVED_FROM_RE.sub("", body)
    body = _DERIVED_METHOD_RE.sub("", body)
    header = f"# Derived-From: {parent}\n# Derived-Method: {method}\n"
    idx = body.find("\nmsgid ")
    if idx == -1:
        return header + body.lstrip("\n")
    return body[: idx + 1] + header + body[idx + 1 :]


def _set_po_language(body: str, child: str) -> str:
    line = f'"Language: {child}\\n"'
    if re.search(r'^"Language:', body, re.MULTILINE):
        return re.sub(
            r'^"Language:[^"]*"',
            lambda _m: line,
            body,
            count=1,
            flags=re.MULTILINE,
        )
    return body.replace(
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        f'"Content-Type: text/plain; charset=UTF-8\\n"\n{line}',
        1,
    )


def _transform_po_body(body: str, child: str, parent: str, method: str) -> str:
    if method == "copy":
        out = body
    elif method.startswith("opencc_"):
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
    out = _set_po_language(out, child)
    return _inject_derived_headers(out, parent, method)


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
    src_po_dir: Path,
    out_po_dir: Path,
    child: str,
    *,
    dry_run: bool = False,
    force: bool = False,
    skip_explicit: bool = False,
    linguas: set[str] | None = None,
) -> tuple[Path | None, bool]:
    """Create derived ``<child>.po`` in *out_po_dir*. Returns (path, written)."""
    child = normalize_locale(child)
    parent = derive_parent(child)
    if parent is None:
        return None, False
    if skip_explicit and linguas and _locale_explicitly_used(child, linguas):
        return None, False
    dest = out_po_dir / f"{child}.po"
    src = _parent_po_path(src_po_dir, out_po_dir, parent)
    if src is None:
        return None, False
    method = DERIVE_METHOD.get(child, "copy")
    if not force and _dest_fresh(dest, src):
        return dest, False
    from ..translate.po_format import po_prepare_utf8, read_po_text

    body = read_po_text(src)
    new_body = _transform_po_body(body, child, parent, method)
    new_body = po_prepare_utf8(new_body)
    if dry_run:
        return dest, True
    out_po_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(new_body, encoding="utf-8")
    return dest, True


def derive_man_file(
    src_docs_dir: Path,
    out_docs_dir: Path,
    stem: str,
    child: str,
    *,
    dry_run: bool = False,
    force: bool = False,
    skip_explicit: bool = False,
    linguas: set[str] | None = None,
) -> tuple[Path | None, bool]:
    """Derive a locale man page. Returns ``(path, written)``."""
    child = normalize_locale(child)
    parent = derive_parent(child)
    if parent is None:
        return None, False
    if skip_explicit and linguas and _locale_explicitly_used(child, linguas):
        return None, False
    dest = out_docs_dir / child / stem
    src = src_docs_dir / parent / stem
    if not src.is_file():
        for alias, target in LEGACY_LOCALE_ALIASES.items():
            if target == parent:
                alt = src_docs_dir / alias / stem
                if alt.is_file():
                    src = alt
                    break
    if not src.is_file():
        built = out_docs_dir / parent / stem
        if built.is_file():
            src = built
    # English whole-document mans often live at docs/*.adoc (not docs/en/).
    if not src.is_file():
        eng = src_docs_dir / stem
        if eng.is_file():
            src = eng
    if not src.is_file():
        return None, False
    method = DERIVE_METHOD.get(child, "copy")
    if not force and _dest_fresh(dest, src):
        return dest, False
    body = src.read_text(encoding="utf-8")
    new_body = _transform_text(body, child, method)
    if dry_run:
        return dest, True
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(new_body, encoding="utf-8")
    return dest, True


def _display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def derive_locales(
    root: Path,
    *,
    po_dir: Path | None = None,
    locales: tuple[str, ...] | None = None,
    dry_run: bool = False,
    force: bool = False,
    skip_explicit: bool = True,
    stamp: Path | None = None,
) -> list[str]:
    """Derive child PO + man pages under the build tree. Returns paths written."""
    targets = locales or tuple(DERIVE_PARENT)
    src_po_dir = root / "po"
    out_po_dir = po_dir or default_build_po_dir(root)
    src_docs = root / "docs"
    out_docs = default_build_docs_dir(root, out_po_dir)
    written: list[str] = []
    linguas: set[str] = set()
    linguas_path = src_po_dir / "LINGUAS"
    if linguas_path.is_file():
        from ..translate.po_files import parse_linguas

        linguas = set(parse_linguas(linguas_path))
    skip = skip_explicit and not force

    for child in targets:
        child = normalize_locale(child)
        if derive_parent(child) is None:
            continue
        if src_po_dir.is_dir():
            po, did_write = derive_po_file(
                src_po_dir,
                out_po_dir,
                child,
                dry_run=dry_run,
                force=force,
                skip_explicit=skip,
                linguas=linguas,
            )
            if po is not None and not dry_run and did_write:
                written.append(_display_path(root, po))
        if src_docs.is_dir():
            for adoc in src_docs.glob("*.adoc"):
                man, did_write = derive_man_file(
                    src_docs,
                    out_docs,
                    adoc.name,
                    child,
                    dry_run=dry_run,
                    force=force,
                    skip_explicit=skip,
                    linguas=linguas,
                )
                if man is not None and not dry_run and did_write:
                    written.append(_display_path(root, man))
    if stamp is not None and not dry_run:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        # Always create/update the Meson output stamp under the build tree.
        stamp.write_text("ok\n", encoding="utf-8")
    return written


def compile_derived_mo(po_dir: Path, domain: str) -> list[str]:
    """Compile flat derived ``*.po`` in *po_dir* when ``.mo`` is older than the ``.po``."""
    msgfmt = shutil.which("msgfmt")
    if msgfmt is None:
        return []
    written: list[str] = []
    for po in sorted(po_dir.glob("*.po")):
        lang = po.stem
        dest = po_dir / lang / "LC_MESSAGES" / f"{domain}.mo"
        if _dest_fresh(dest, po):
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run([msgfmt, "-o", str(dest), str(po)], check=False)
        if proc.returncode != 0:
            continue
        written.append(str(dest))
    return written


def install_derived_mo(
    po_dir: Path,
    domain: str,
    *,
    localedir: str = "share/locale",
    dest_root: Path | None = None,
) -> list[str]:
    """Install ``.mo`` for each flat derived ``*.po`` under *po_dir*.

    *dest_root* defaults to ``$MESON_INSTALL_DESTDIR_PREFIX`` or
    ``$DESTDIR$MESON_INSTALL_PREFIX`` (Meson install-script environment).
    """
    if dest_root is None:
        combined = os.environ.get("MESON_INSTALL_DESTDIR_PREFIX")
        if combined:
            dest_root = Path(combined)
        else:
            destdir = os.environ.get("DESTDIR", "")
            prefix = os.environ.get("MESON_INSTALL_PREFIX", "")
            dest_root = Path(destdir + prefix)
    if not str(dest_root):
        return []
    installed: list[str] = []
    for po in sorted(po_dir.glob("*.po")):
        lang = po.stem
        mo = po_dir / lang / "LC_MESSAGES" / f"{domain}.mo"
        if not mo.is_file():
            continue
        dest = dest_root / localedir / lang / "LC_MESSAGES" / f"{domain}.mo"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mo, dest)
        installed.append(str(dest))
    return installed


def derive_children_of(
    root: Path,
    parent: str,
    *,
    po_dir: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
    skip_explicit: bool = True,
    stamp: Path | None = None,
) -> list[str]:
    return derive_locales(
        root,
        po_dir=po_dir,
        locales=children_of(parent),
        dry_run=dry_run,
        force=force,
        skip_explicit=skip_explicit,
        stamp=stamp,
    )
