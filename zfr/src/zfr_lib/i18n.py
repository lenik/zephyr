# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext helpers for the zfr CLI (domain: zfr)."""

from __future__ import annotations

import gettext
import locale
import os
import subprocess
from pathlib import Path

_DOMAIN = "zfr"
_translation: gettext.NullTranslations | None = None


def _wanted_languages() -> list[str] | None:
    """Expand LANG/LANGUAGE into gettext catalog names (zh → zh_CN)."""
    raw = (
        os.environ.get("LANGUAGE")
        or os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or ""
    )
    if not raw:
        return None
    out: list[str] = []
    seen: set[str] = set()

    def add(tag: str) -> None:
        tag = tag.strip()
        if not tag or tag in seen:
            return
        seen.add(tag)
        out.append(tag)

    for part in raw.split(":"):
        part = part.split(".")[0].split("@")[0].strip().replace("-", "_")
        if not part or part in ("C", "POSIX"):
            continue
        lower = part.lower()
        add(part)
        if lower in {"zh", "zh_hans", "zh_cn", "zh_sg"}:
            add("zh_CN")
            add("zh")
        elif lower in {"zh_hant", "zh_tw", "zh_hk"}:
            add("zh_TW")
            add("zh")
        elif "_" in part:
            add(part.split("_", 1)[0])
    return out or None


def _source_root() -> Path:
    # zfr/src/zfr_lib/i18n.py → zfr/
    return Path(__file__).resolve().parents[2]


def _compile_po_tree(po_dir: Path) -> Path | None:
    """msgfmt zfr/po/*.po into a cache dir that gettext can consume."""
    pos = sorted(po_dir.glob("*.po"))
    if not pos:
        return None
    cache_root = Path(
        os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
    ) / "zfr" / "locale"
    msgfmt = shutil_which("msgfmt")
    if msgfmt is None:
        return None
    wrote = False
    for po in pos:
        loc = po.stem
        dest_dir = cache_root / loc / "LC_MESSAGES"
        dest = dest_dir / f"{_DOMAIN}.mo"
        try:
            po_mtime = po.stat().st_mtime
            if dest.is_file() and dest.stat().st_mtime >= po_mtime:
                wrote = True
                continue
        except OSError:
            pass
        dest_dir.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [msgfmt, "-o", str(dest), str(po)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and dest.is_file():
            wrote = True
    return cache_root if wrote else None


def shutil_which(name: str) -> str | None:
    from shutil import which

    return which(name)


def _locale_dirs() -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("ZFR_LOCALEDIR") or os.environ.get("ZEPHYR_LOCALEDIR")
    if env:
        dirs.append(Path(env))

    here = Path(__file__).resolve()
    zfr_root = here.parents[2]
    repo = zfr_root.parent
    # Prefer catalogs compiled from the source po/ tree so uninstalled
    # `zfr -h` tracks the current strings (not a stale meson builddir).
    compiled = _compile_po_tree(zfr_root / "po")
    if compiled is not None:
        dirs.append(compiled)
    meson_root = os.environ.get("MESON_BUILD_ROOT")
    if meson_root:
        dirs.append(Path(meson_root) / "po")
    dirs.extend(
        [
            Path("/build/po"),
            zfr_root / "build" / "po",
            repo / "build" / "po",
            repo / "debian" / "build" / "po",
        ]
    )
    try:
        from . import paths_config  # type: ignore

        pkg = Path(paths_config.PKGDATADIR)
        dirs.append(pkg / "locale")
    except Exception:
        pass
    dirs.append(Path("/usr/share/locale"))
    dirs.append(Path("/usr/local/share/locale"))
    # unique, keep order
    seen: set[Path] = set()
    out: list[Path] = []
    for d in dirs:
        try:
            key = d.resolve()
        except OSError:
            key = d
        if key in seen or not d.exists():
            continue
        seen.add(key)
        out.append(d)
    return out


def init_i18n() -> None:
    """Bind the zfr message domain (safe to call multiple times)."""
    global _translation
    if _translation is not None:
        return
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass
    langs = _wanted_languages()
    kwargs: dict[str, object] = {"fallback": False}
    if langs:
        kwargs["languages"] = langs
    for d in _locale_dirs():
        try:
            _translation = gettext.translation(
                _DOMAIN, localedir=str(d), **kwargs  # type: ignore[arg-type]
            )
            _translation.install()
            return
        except FileNotFoundError:
            continue
        except OSError:
            continue
    _translation = gettext.NullTranslations()
    _translation.install()


def _(message: str) -> str:
    init_i18n()
    assert _translation is not None
    return _translation.gettext(message)
