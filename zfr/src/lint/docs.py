# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-rule documentation for lint browse — loaded from lint_rules*.md."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from i18n import _
from std import LINT_RULES, StdRule
from .ize_map import ize_command_for_lint, ize_targets_for_lint

Section = tuple[str, str]  # (heading, body)


@dataclass(frozen=True)
class RuleDoc:
    sections: tuple[Section, ...]


_HEADING_RE = re.compile(r"^##\s+(\S+)\s*$")
_SUB_RE = re.compile(r"^###\s+(.+?)(?:\s+\{(\w+)\})?\s*$")
_ID_RE = re.compile(r"^([A-Za-z]+)-?(\d+)$")


def _docs_dir() -> Path:
    return Path(__file__).resolve().parent


def format_rule_heading(rule_id: str) -> str:
    """Normalize to ``ZL0001`` (no hyphen) for markdown headings."""
    m = _ID_RE.fullmatch(rule_id.strip())
    if not m:
        return rule_id
    return f"{m.group(1)}{int(m.group(2)):04d}"


def normalize_rule_heading(token: str) -> str:
    """``ZL0001`` / ``ZL-0001`` / ``zl-1`` → ``ZL0001``."""
    m = _ID_RE.fullmatch(token.strip())
    if not m:
        return token.strip().upper()
    return f"{m.group(1).upper()}{int(m.group(2)):04d}"


def locale_fallback_chain(lang: str) -> list[str]:
    """``zh_CN`` → ``[zh_CN, zh]``; ``de_AT`` → ``[de_AT, de]``; ``en`` → ``[]``."""
    norm = (lang or "").strip().replace("-", "_")
    if not norm or norm.lower() in ("en", "c", "posix"):
        return []
    chain = [norm]
    if "_" in norm:
        chain.append(norm.split("_", 1)[0])
    # Deduplicate while preserving order.
    out: list[str] = []
    for item in chain:
        if item and item not in out:
            out.append(item)
    return out


def _candidate_paths(lang: str) -> list[Path]:
    """``lint_rules-zh.md`` (from zh_CN) → ``lint_rules.md``.

    Region tags fall back to the language only — maintain ``lint_rules-zh.md``,
    not a separate ``lint_rules-zh_CN.md``.
    """
    base = _docs_dir()
    paths: list[Path] = []
    for loc in locale_fallback_chain(lang):
        paths.append(base / f"lint_rules-{loc}.md")
    paths.append(base / "lint_rules.md")
    return paths


@dataclass
class _Block:
    key: str  # rule id ZL0001, family:debian, ize, ize:none
    sections: list[Section]


def _parse_markdown(text: str) -> dict[str, list[Section]]:
    blocks: dict[str, list[Section]] = {}
    current_key: str | None = None
    current_title = ""
    body_lines: list[str] = []

    def flush_section() -> None:
        nonlocal current_title, body_lines
        if current_key is None:
            current_title = ""
            body_lines = []
            return
        body = "\n".join(body_lines).strip()
        title = current_title.strip()
        if title or body:
            blocks.setdefault(current_key, []).append(
                (title or _("Documentation"), body or title)
            )
        current_title = ""
        body_lines = []

    def flush_all() -> None:
        flush_section()

    for raw in text.splitlines():
        hm = _HEADING_RE.match(raw)
        if hm:
            flush_all()
            token = hm.group(1)
            if token.startswith("family:"):
                current_key = token
            elif token == "ize":
                current_key = "ize"
            else:
                current_key = normalize_rule_heading(token)
            continue
        sm = _SUB_RE.match(raw)
        if sm:
            flush_section()
            current_title = sm.group(1).strip()
            sid = (sm.group(2) or "").strip()
            if current_key == "ize" and sid:
                current_key = f"ize:{sid}"
            continue
        if current_key is None:
            continue
        body_lines.append(raw)
    flush_all()
    return blocks


@dataclass(frozen=True)
class _Catalog:
    rules: dict[str, list[Section]]
    families: list[tuple[str, list[Section]]]
    ize_solve: list[Section]
    ize_none: list[Section]


def _blocks_to_catalog(blocks: dict[str, list[Section]]) -> _Catalog:
    rules: dict[str, list[Section]] = {}
    fam_map: dict[str, list[Section]] = {}
    ize_solve: list[Section] = []
    ize_none: list[Section] = []
    for key, secs in blocks.items():
        if key.startswith("family:"):
            label = key[len("family:") :]
            prefix = "" if label == "generic" else (label if label.endswith(".") else label + ".")
            fam_map[prefix] = secs
        elif key == "ize:none":
            ize_none = secs
        elif key == "ize":
            ize_solve = secs
        elif key.startswith("ize:"):
            ize_none = secs if key.endswith("none") else ize_solve
        else:
            rules[key] = secs
    families = sorted(fam_map.items(), key=lambda x: len(x[0]), reverse=True)
    return _Catalog(rules, families, ize_solve, ize_none)


def _parse_file(path: Path) -> _Catalog | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return _blocks_to_catalog(_parse_markdown(text))


@lru_cache(maxsize=32)
def _load_merged(lang: str) -> _Catalog:
    """Merge locale overlays onto English ``lint_rules.md``.

    Lookup order for files: ``lint_rules-<full>.md``, ``lint_rules-<lang>.md``,
    then English. Later files only fill missing keys (first hit wins per key).
    """
    en = _parse_file(_docs_dir() / "lint_rules.md") or _Catalog({}, [], [], [])
    rules = dict(en.rules)
    fam_map = {p: list(s) for p, s in en.families}
    ize_solve = list(en.ize_solve)
    ize_none = list(en.ize_none)

    # Apply locale files from most specific to language-only; do not re-read English.
    for path in _candidate_paths(lang):
        if path.name == "lint_rules.md":
            continue
        loc = _parse_file(path)
        if loc is None:
            continue
        for rid, secs in loc.rules.items():
            rules[rid] = secs
        for prefix, secs in loc.families:
            fam_map[prefix] = secs
        if loc.ize_solve:
            ize_solve = list(loc.ize_solve)
        if loc.ize_none:
            ize_none = list(loc.ize_none)
    families = sorted(fam_map.items(), key=lambda x: len(x[0]), reverse=True)
    return _Catalog(rules, families, ize_solve, ize_none)


def _current_lang() -> str:
    for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        raw = os.environ.get(key) or ""
        if not raw:
            continue
        token = raw.split(":", 1)[0].strip()
        if token:
            return token.split(".", 1)[0]
    return "en"


def _format_sections(sections: list[Section], mapping: dict[str, str]) -> list[Section]:
    out: list[Section] = []
    for title, body in sections:
        try:
            t = title.format_map(mapping)
            b = body.format_map(mapping)
        except (KeyError, ValueError):
            t, b = title, body
        out.append((t, b))
    return out


def _family_sections(code: str, rule: StdRule, cat: _Catalog) -> list[Section] | None:
    # Short title stays gettext; essays come from markdown.
    title = _(rule.title)
    detail = _(rule.detail).strip() if rule.detail else ""
    if not detail:
        detail = _("Checker `%s` in `zfr lint`.") % rule.code
    sev = rule.default_severity or _("varies")
    mapping = {
        "title": title,
        "detail": detail,
        "sev": sev,
        "code": rule.code,
        "id": rule.id,
    }
    for prefix, sections in cat.families:
        if prefix == "" or code.startswith(prefix):
            return _format_sections(sections, mapping)
    return None


def _ize_sections(code: str, cat: _Catalog) -> list[Section]:
    targets = ize_targets_for_lint(code)
    cmd = ize_command_for_lint(code)
    if not targets:
        if cat.ize_none:
            return list(cat.ize_none)
        return [
            (
                _("No Solve mapping"),
                _(
                    "This finding has no `zfr ize --only …` shortcut. Follow the "
                    "fix text (or a broader `zfr ize` if several related gaps "
                    "exist), then re-lint."
                ),
            )
        ]
    mapping = {"targets": ", ".join(targets), "cmd": cmd or ""}
    if cat.ize_solve:
        return _format_sections(list(cat.ize_solve), mapping)
    return [
        (
            _("Solve / ize"),
            _(
                "Clicking Solve runs only: %(targets)s.\n"
                "Equivalent CLI: `%(cmd)s`\n"
                "Use `-n` for a dry plan. Output is captured with fdmux "
                "(ordered stdout/stderr)."
            )
            % mapping,
        )
    ]


def rule_doc_for(rule_id: str, code: str, *, lang: str | None = None) -> RuleDoc:
    rule = LINT_RULES.by_id(rule_id) or LINT_RULES.lookup(code)
    if rule is None:
        rule = StdRule(rule_id, code, code)

    cat = _load_merged(lang if lang is not None else _current_lang())
    ov = cat.rules.get(rule.id) or cat.rules.get(normalize_rule_heading(rule_id))
    if ov:
        sections = list(ov)
    else:
        sections = _family_sections(code, rule, cat) or []

    ize = _ize_sections(code, cat)
    already = any(
        "olve" in (t + b).lower() or "ize" in (t + b).lower() for t, b in sections
    )
    if not already:
        sections.extend(ize)

    cleaned: list[Section] = []
    for title, body in sections:
        t = title.strip()
        b = body.strip()
        if t and b:
            cleaned.append((t, b))
    return RuleDoc(sections=tuple(cleaned))


def rule_doc_dict(
    rule_id: str, code: str, *, lang: str | None = None
) -> dict[str, object]:
    d = rule_doc_for(rule_id, code, lang=lang)
    # Browse chrome: include gettext short title separately from MD essays.
    rule = LINT_RULES.by_id(rule_id) or LINT_RULES.lookup(code)
    short = _(rule.title) if rule else code
    return {
        "title": short,
        "sections": [{"title": t, "body": b} for t, b in d.sections],
    }


def clear_doc_cache() -> None:
    _load_merged.cache_clear()
