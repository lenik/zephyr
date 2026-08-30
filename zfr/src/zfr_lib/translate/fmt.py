# SPDX-License-Identifier: AGPL-3.0-or-later
"""Colored output helpers for zfr translate."""

from __future__ import annotations

import colorsys

from ..l10n import normalize_locale

_RESET = "\033[0m"
_KEY_FG = "\033[1;33m"  # bold yellow — msgid / key text
_SEP_FG = "\033[2m"  # dim — punctuation (':', '=>')
_STRIPE_EVEN = "\033[2m"  # dim
_STRIPE_ODD = "\033[36m"  # cyan


def locale_hue(locale: str) -> float:
    """Stable hue in [0, 1) from a gettext locale code."""
    loc = normalize_locale(locale)
    return (hash(loc) & 0xFFFFFFFF) / 0x100000000


def locale_fg(locale: str, *, on: bool) -> str:
    if not on:
        return ""
    r, g, b = colorsys.hls_to_rgb(locale_hue(locale), 0.58, 0.72)
    return f"\033[38;2;{int(r * 255)};{int(g * 255)};{int(b * 255)}m"


def stripe_fg(index: int, *, on: bool) -> str:
    if not on:
        return ""
    return _STRIPE_EVEN if index % 2 == 0 else _STRIPE_ODD


def paint(text: str, fg: str) -> str:
    if not fg:
        return text
    return f"{fg}{text}{_RESET}"


def paint_key(text: str, *, on: bool) -> str:
    return paint(text, _KEY_FG if on else "")


def paint_sep(text: str, *, on: bool) -> str:
    return paint(text, _SEP_FG if on else "")


def paint_locale_label(label: str, locale: str, *, on: bool) -> str:
    return paint(label, locale_fg(locale, on=on))


def paint_translation(text: str, locale: str, *, on: bool) -> str:
    return paint(text, locale_fg(locale, on=on))
