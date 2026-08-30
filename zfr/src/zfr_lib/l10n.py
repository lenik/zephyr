# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext / manpage locale tiers, fallback matrix, and lint coverage levels."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

from .cmd_options import LINT_OPTIONS_REL, load_option_tokens

# Canonical gettext source language (conceptually en-US).
SOURCE_LOCALE = "en"

# Tier I — EFIGS, CJK, Ar (primary locales only; children are auto-derived).
TIER_I: tuple[str, ...] = (
    "fr",
    "it",
    "de",
    "es_MX",
    "zh_CN",
    "ja",
    "ko",
    "ar",
)

# Tier II — Southeast Asia, popular Europe, populous nations.
TIER_II: tuple[str, ...] = (
    "id",
    "vi",
    "th",
    "pt_BR",
    "nl",
    "pl",
    "tr",
    "ru",
    "hi",
)

# Tier III — Nordic, EU compliance, Asia-Pacific / South Asia, Middle East.
TIER_III: tuple[str, ...] = (
    "sv",
    "no",
    "da",
    "fi",
    "cs",
    "ro",
    "el",
    "hu",
    "bg",
    "uk",
    "kk",
    "fil_PH",
    "bn",
    "mr",
    "ta",
    "te",
    "he",
    "sw",
)

# Lint coverage levels (primary locales only; derived locales satisfy via parent).
L10N_LEVELS: dict[str, tuple[str, ...]] = {
    "L0": (),
    "L1": TIER_I,
    "L2": TIER_I + TIER_II,
    "L3": TIER_I + TIER_II + TIER_III,
}

# Older trees may still use these names in po/LINGUAS.
LEGACY_LOCALE_ALIASES: dict[str, str] = {
    "es": "es_MX",
    "pt": "pt_BR",
    "en_US": SOURCE_LOCALE,
}

# Direct parent for ``->`` auto-generation (child -> parent).
DERIVE_PARENT: dict[str, str] = {
    "en_GB": SOURCE_LOCALE,
    "en_AU": "en_GB",
    "en_CA": SOURCE_LOCALE,
    "fr_CH": "fr",
    "fr_BE": "fr",
    "fr_CA": "fr",
    "de_CH": "de",
    "de_AT": "de",
    "lb": "de",
    "es_ES": "es_MX",
    "es_US": "es_MX",
    "zh_TW": "zh_CN",
    "zh_HK": "zh_TW",
    "zh_SG": "zh_CN",
    "ar_AE": "ar",
    "ar_SA": "ar",
    "ar_EG": "ar",
    "ms": "id",
    "pt_PT": "pt_BR",
    "az": "tr",
    "be": "ru",
    "ne": "hi",
    "tl_PH": "fil_PH",
}

# Static conversion method per derived locale (no AI; copy when unknown).
DERIVE_METHOD: dict[str, str] = {
    "zh_TW": "opencc_s2t",
    "zh_HK": "opencc_s2hk",
    "zh_SG": "copy",
    "lb": "copy",
    "ms": "copy",
    "az": "copy",
    "be": "copy",
    "ne": "copy",
    "tl_PH": "copy",
}

# Runtime fallback chain (gettext names; terminal ``en`` is the msgid source).
FALLBACK_LNGS: dict[str, tuple[str, ...]] = {
    "en_GB": (SOURCE_LOCALE,),
    "en_AU": ("en_GB", SOURCE_LOCALE),
    "en_CA": (SOURCE_LOCALE,),
    "es_ES": ("es_MX", SOURCE_LOCALE),
    "es_US": ("es_MX", SOURCE_LOCALE),
    "zh_TW": ("zh_CN",),
    "zh_HK": ("zh_TW", "zh_CN"),
    "zh_SG": ("zh_CN",),
    "ms": ("id", SOURCE_LOCALE),
    "pt_PT": ("pt_BR", SOURCE_LOCALE),
    "fil_PH": ("tl_PH", SOURCE_LOCALE),
    "tl_PH": (SOURCE_LOCALE,),
    "bn": (SOURCE_LOCALE,),
    "mr": ("hi", SOURCE_LOCALE),
    "ta": (SOURCE_LOCALE,),
    "te": (SOURCE_LOCALE,),
    "sv": (SOURCE_LOCALE,),
    "no": (SOURCE_LOCALE,),
    "da": (SOURCE_LOCALE,),
    "fi": (SOURCE_LOCALE,),
    "ro": (SOURCE_LOCALE,),
    "cs": (SOURCE_LOCALE,),
    "el": (SOURCE_LOCALE,),
    "hu": (SOURCE_LOCALE,),
    "bg": (SOURCE_LOCALE,),
    "uk": ("ru", SOURCE_LOCALE),
    "kk": ("ru", SOURCE_LOCALE),
    "he": (SOURCE_LOCALE,),
    "default": (SOURCE_LOCALE,),
}

# Sub-tier labels (primary locale -> "1.1" style).
LOCALE_TIER_LABEL: dict[str, str] = {
    SOURCE_LOCALE: "1.0",
    "fr": "1.1",
    "it": "1.1",
    "de": "1.1",
    "es_MX": "1.1",
    "zh_CN": "1.2",
    "ja": "1.2",
    "ko": "1.2",
    "ar": "1.3",
    "id": "2.1",
    "vi": "2.1",
    "th": "2.1",
    "pt_BR": "2.2",
    "nl": "2.3",
    "pl": "2.3",
    "tr": "2.3",
    "ru": "2.4",
    "hi": "2.5",
    "sv": "3.1",
    "no": "3.1",
    "da": "3.1",
    "fi": "3.1",
    "cs": "3.2",
    "ro": "3.2",
    "el": "3.2",
    "hu": "3.2",
    "bg": "3.2",
    "uk": "3.2",
    "kk": "3.2",
    "fil_PH": "3.3",
    "bn": "3.3",
    "mr": "3.3",
    "ta": "3.3",
    "te": "3.3",
    "he": "3.4",
    "sw": "3.5",
}

# BCP-47 display overrides (web tag -> gettext name in parentheses).
DISPLAY_BCP47: dict[str, str] = {
    "es_MX": "es-419",
}

EN_MAN_NAME = "zfr - multi-language CLI project templates and helper tools"


def normalize_locale(tag: str) -> str:
    """Map BCP-47 or legacy aliases to canonical gettext locale names."""
    raw = tag.strip().replace("-", "_")
    if not raw:
        return raw
    parts = raw.split("_", 1)
    lang = parts[0].lower()
    if len(parts) == 1:
        key = lang
    else:
        region = parts[1]
        if len(region) == 2:
            region = region.upper()
        elif region.isdigit() or region.upper() in {"419"}:
            region = region.upper()
        key = f"{lang}_{region}"
    aliases = {
        "en_us": SOURCE_LOCALE,
        "en": SOURCE_LOCALE,
        "es": "es_MX",
        "es_419": "es_MX",
        "pt": "pt_BR",
        "fil": "fil_PH",
        "tl": "tl_PH",
        "no": "no",
        "nb": "no",
        "nn": "no",
    }
    return aliases.get(key.lower(), key if "_" in key else lang)


def to_bcp47(tag: str) -> str:
    """gettext name -> BCP-47 (hyphenated) for display."""
    loc = normalize_locale(tag)
    if loc in DISPLAY_BCP47:
        return DISPLAY_BCP47[loc]
    if loc == SOURCE_LOCALE:
        return "en-US"
    if "_" not in loc:
        return loc
    lang, region = loc.split("_", 1)
    return f"{lang}-{region}"


def format_locale_display(tag: str) -> str:
    """Display as ``es-419 (es_MX)`` — BCP-47 tag, then gettext name."""
    loc = tag.strip()
    norm = normalize_locale(loc)
    bcp = DISPLAY_BCP47.get(norm, to_bcp47(norm))
    return f"{bcp} ({loc})"


def primary_locales() -> tuple[str, ...]:
    return TIER_I + TIER_II + TIER_III


def derived_locales() -> tuple[str, ...]:
    return tuple(sorted(DERIVE_PARENT))


def all_locales() -> tuple[str, ...]:
    return (SOURCE_LOCALE,) + primary_locales() + derived_locales()


def canonical_locale(tag: str) -> str:
    """Resolve legacy aliases to canonical primary names."""
    loc = normalize_locale(tag)
    return LEGACY_LOCALE_ALIASES.get(loc, loc)


def resolve_present_locale(loc: str, present: set[str]) -> str | None:
    """Return the catalog name in *present* that satisfies *loc* (direct or legacy)."""
    loc = canonical_locale(normalize_locale(loc))
    if loc in present:
        return loc
    for alias, target in LEGACY_LOCALE_ALIASES.items():
        if target == loc and alias in present:
            return alias
    for fb in fallback_chain(loc):
        if fb in present:
            return fb
        for alias, target in LEGACY_LOCALE_ALIASES.items():
            if target == fb and alias in present:
                return alias
    return None


def fallback_chain(locale: str) -> tuple[str, ...]:
    """Ordered fallback targets for *locale* (not including *locale* itself)."""
    loc = normalize_locale(locale)
    out: list[str] = []
    seen: set[str] = {loc}

    def extend(chain: tuple[str, ...]) -> None:
        for item in chain:
            item = canonical_locale(item)
            if item not in seen:
                seen.add(item)
                out.append(item)

    extend(FALLBACK_LNGS.get(loc, ()))
    extend(FALLBACK_LNGS.get("default", (SOURCE_LOCALE,)))
    return tuple(out)


def derive_parent(locale: str) -> str | None:
    loc = normalize_locale(locale)
    parent = DERIVE_PARENT.get(loc)
    if parent is None:
        return None
    return canonical_locale(parent)


def children_of(locale: str) -> tuple[str, ...]:
    loc = canonical_locale(normalize_locale(locale))
    return tuple(sorted(child for child, parent in DERIVE_PARENT.items() if parent == loc))


def parse_l10n_level(value: str) -> str:
    """Accept L0–L3 or 0–3. Raises argparse.ArgumentTypeError on junk."""
    raw = str(value).strip().upper().replace(" ", "")
    if raw.isdigit():
        raw = f"L{int(raw)}"
    if raw not in L10N_LEVELS:
        raise argparse.ArgumentTypeError(
            f"l10n level must be L0–L3 (or 0–3), not {value!r}"
        )
    return raw


def linguas_for_level(level: str) -> tuple[str, ...]:
    return L10N_LEVELS[parse_l10n_level(level)]


def lint_options_path(root: Path) -> Path:
    return root / LINT_OPTIONS_REL


def load_lint_option_tokens(root: Path) -> list[str]:
    """Tokens from packagedir/.config/zfr/lint.options (comments allowed)."""
    return load_option_tokens(root, LINT_OPTIONS_REL)


def apply_lint_option_file(
    root: Path,
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> argparse.Namespace:
    """Fill argparse defaults from lint.options. CLI values already on *args* win."""
    tokens = load_lint_option_tokens(root)
    if not tokens:
        if getattr(args, "l10n_level", None) is None:
            args.l10n_level = "L1"
        return args
    cfg = parser.parse_args(tokens)
    if getattr(args, "l10n_level", None) is None:
        args.l10n_level = getattr(cfg, "l10n_level", None) or "L1"
    args.verbose = bool(args.verbose or cfg.verbose)
    args.quiet = bool(args.quiet or cfg.quiet)
    args.strict = bool(args.strict or cfg.strict)
    if args.color == "auto" and cfg.color != "auto":
        args.color = cfg.color
    if getattr(cfg, "uncheck", None):
        merged = list(getattr(args, "uncheck", None) or [])
        for item in cfg.uncheck:
            if item not in merged:
                merged.append(item)
        args.uncheck = merged
    if args.style_info is None and getattr(cfg, "style_info", None) is not None:
        args.style_info = cfg.style_info
    return args
