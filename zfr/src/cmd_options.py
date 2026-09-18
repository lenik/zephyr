# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project option files for zfr subcommands (.config/zfr/*.options)."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

LINT_OPTIONS_REL = Path(".config") / "zfr" / "lint.options"
IZE_OPTIONS_REL = Path(".config") / "zfr" / "ize.options"


def options_path(root: Path, rel: Path) -> Path:
    return root / rel


def load_option_tokens(root: Path, rel: Path) -> list[str]:
    path = options_path(root, rel)
    if not path.is_file():
        return []
    tokens: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            tokens.extend(shlex.split(line))
    return tokens


def apply_option_file(
    root: Path,
    rel: Path,
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    *,
    merge_flags: tuple[str, ...] = (),
) -> argparse.Namespace:
    """Fill argparse defaults from an options file. Explicit CLI values win."""
    tokens = load_option_tokens(root, rel)
    cfg: argparse.Namespace | None = None
    if tokens:
        cfg = parser.parse_args(tokens)
    if cfg is None:
        return args
    for key, value in vars(cfg).items():
        if key in merge_flags:
            cur = getattr(args, key, None)
            if cur:
                merged = list(cur)
                extra = getattr(cfg, key, None) or []
                for item in extra:
                    if item not in merged:
                        merged.append(item)
                setattr(args, key, merged)
            elif getattr(cfg, key, None):
                setattr(args, key, getattr(cfg, key))
            continue
        if getattr(args, key, None) in (None, False, "auto", []):
            setattr(args, key, value)
    return args
