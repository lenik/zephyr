# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext helpers for the zfr CLI (domain: zfr)."""

from __future__ import annotations

import gettext
import locale
import os
from pathlib import Path

_DOMAIN = "zfr"
_translation: gettext.NullTranslations | None = None


def _locale_dirs() -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("ZFR_LOCALEDIR") or os.environ.get("ZEPHYR_LOCALEDIR")
    if env:
        dirs.append(Path(env))
    here = Path(__file__).resolve().parent
    # tools/zfr_lib → tools/po (source tree) or share/locale (installed)
    tools = here.parent
    dirs.append(tools / "po")
    try:
        from . import paths_config  # type: ignore

        pkg = Path(paths_config.PKGDATADIR)
        dirs.append(pkg / "locale")
        dirs.append(Path("/usr/share/locale"))
    except Exception:
        dirs.append(Path("/usr/share/locale"))
        dirs.append(Path("/usr/local/share/locale"))
    return dirs


def init_i18n() -> None:
    """Bind the zfr message domain (safe to call multiple times)."""
    global _translation
    if _translation is not None:
        return
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass
    for d in _locale_dirs():
        try:
            _translation = gettext.translation(
                _DOMAIN, localedir=str(d), fallback=False
            )
            _translation.install()
            return
        except FileNotFoundError:
            continue
    _translation = gettext.NullTranslations()
    _translation.install()


def _(message: str) -> str:
    init_i18n()
    assert _translation is not None
    return _translation.gettext(message)
