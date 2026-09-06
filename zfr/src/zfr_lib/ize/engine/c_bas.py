# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize: C-family bas i18n / logger / LOCALEDIR / gettext spacing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...lang._c_bas import (
    C_FAMILY_LANGS,
    bas_build_depends,
    ensure_define_logger,
    ensure_main_bas_i18n,
    ensure_meson_bas_dep,
    ensure_meson_localedir,
    find_main_sources,
    fix_gettext_edge_spaces,
    has_define_logger,
    logger_target_file,
    prefer_weak_logger,
    _src_files,
)
from ..debian import ensure_build_depends
from ..util import *  # noqa: F403

if TYPE_CHECKING:
    from . import Ize


def ensure_c_bas(ize: "Ize") -> None:
    """Bring C-family sources/meson/debian up to bas i18n + logger conventions."""
    if ize.lang not in C_FAMILY_LANGS:
        return

    for path in find_main_sources(ize.root):
        text = path.read_text(encoding="utf-8")
        new, notes = ensure_main_bas_i18n(text)
        if new != text:
            ize.write_text(path, new, "; ".join(notes) or "bas i18n main setup")

    if has_define_logger(ize.root) is None:
        target = logger_target_file(ize.root, ize.lang)
        if target is not None and target.is_file():
            text = target.read_text(encoding="utf-8")
            new, notes = ensure_define_logger(
                text, weak=prefer_weak_logger(ize.lang, ize.root)
            )
            if new != text:
                ize.write_text(target, new, "; ".join(notes) or "define_logger()")

    for path in _src_files(ize.root):
        text = path.read_text(encoding="utf-8")
        new, n = fix_gettext_edge_spaces(text)
        if n:
            ize.write_text(
                path,
                new,
                f"strip leading/trailing spaces in {n} gettext string(s)",
            )

    meson = ize.root / "meson.build"
    if meson.is_file():
        text = meson.read_text(encoding="utf-8")
        new, notes = ensure_meson_localedir(text)
        new2, notes2 = ensure_meson_bas_dep(new, lang=ize.lang)
        notes = notes + notes2
        if new2 != text:
            ize.write_text(meson, new2, "; ".join(notes) or "LOCALEDIR + bas dep")

    control = ize.root / "debian" / "control"
    if control.is_file():
        extras = tuple(bas_build_depends(ize.lang))
        text = control.read_text(encoding="utf-8")
        new, notes = ensure_build_depends(text, extras=extras)
        if notes:
            ize.write_text(control, new, "; ".join(notes))
