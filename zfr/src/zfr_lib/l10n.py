# SPDX-License-Identifier: AGPL-3.0-or-later
"""gettext / manpage locale coverage levels for zfr lint."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

L10N_LEVELS: dict[str, tuple[str, ...]] = {
    "L0": (),
    "L1": (
        "de",
        "es",
        "fr",
        "it",
        "ja",
        "ko",
        "pl",
        "ru",
        "zh_CN",
        "zh_TW",
    ),
    "L2": (
        "bg",
        "ca",
        "cs",
        "de",
        "el",
        "es",
        "fr",
        "hu",
        "id",
        "it",
        "ja",
        "ko",
        "nl",
        "pl",
        "pt",
        "ru",
        "sv",
        "tr",
        "zh_CN",
        "zh_TW",
    ),
    "L3": (
        "bg",
        "ca",
        "cs",
        "da",
        "de",
        "el",
        "es",
        "et",
        "fi",
        "fr",
        "gl",
        "hr",
        "hu",
        "id",
        "it",
        "ja",
        "ko",
        "lt",
        "ms",
        "nl",
        "pl",
        "pt",
        "pt_BR",
        "ru",
        "sk",
        "sl",
        "sv",
        "tr",
        "zh_CN",
        "zh_TW",
    ),
}

LINT_OPTIONS_REL = Path(".config") / "zfr" / "lint.options"
EN_MAN_NAME = "zfr - multi-language CLI project templates and helper tools"


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
    path = lint_options_path(root)
    if not path.is_file():
        return []
    tokens: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            tokens.extend(shlex.split(line))
    return tokens


def apply_lint_option_file(
    root: Path,
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> argparse.Namespace:
    """Fill argparse defaults from lint.options. CLI values already on *args* win."""
    tokens = load_lint_option_tokens(root)
    cfg: argparse.Namespace | None = None
    if tokens:
        cfg = parser.parse_args(tokens)
    if getattr(args, "l10n_level", None) is None:
        args.l10n_level = (cfg.l10n_level if cfg is not None else None) or "L1"
    if cfg is None:
        return args
    args.verbose = bool(args.verbose or cfg.verbose)
    args.quiet = bool(args.quiet or cfg.quiet)
    args.strict = bool(args.strict or cfg.strict)
    if args.color == "auto" and cfg.color != "auto":
        args.color = cfg.color
    return args
