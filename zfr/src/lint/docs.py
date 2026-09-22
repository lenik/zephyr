# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-rule documentation for lint browse — loaded from lint/rules/ZL*/README*.md."""

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


_ID_RE = re.compile(r"^([A-Za-z]+)-?(\d+)$")
_SUB_RE = re.compile(r"^###\s+(.+?)\s*$")
_H1_RE = re.compile(r"^#\s+(.+?)\s*$")


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
    # zh → also try zh_CN README name
    if norm == "zh" or norm.startswith("zh_"):
        if "zh_CN" not in chain:
            chain.insert(0 if norm == "zh" else len(chain), "zh_CN")
    out: list[str] = []
    for item in chain:
        if item and item not in out:
            out.append(item)
    return out


def _rule_dir(rule_id: str) -> Path:
    rid = normalize_rule_heading(rule_id)
    lint_d = Path(__file__).resolve().parent / "rules" / rid
    if lint_d.is_dir():
        return lint_d
    ize_d = Path(__file__).resolve().parent.parent / "ize" / "rules" / rid
    if ize_d.is_dir():
        return ize_d
    return lint_d


def _readme_candidates(rule_id: str, lang: str) -> list[Path]:
    d = _rule_dir(rule_id)
    paths: list[Path] = []
    for loc in locale_fallback_chain(lang):
        paths.append(d / f"README-{loc}.md")
        # also try language-only alias used historically
        if "_" in loc:
            paths.append(d / f"README-{loc.split('_', 1)[0]}.md")
    paths.append(d / "README.md")
    return paths


def _parse_readme(text: str) -> list[Section]:
    """Split a rule README into sections (### headings; leading # is title)."""
    lines = text.splitlines()
    sections: list[Section] = []
    title = ""
    current = ""
    body: list[str] = []

    def flush() -> None:
        nonlocal current, body
        b = "\n".join(body).strip()
        if current or b:
            sections.append((current or _("Documentation"), b))
        current = ""
        body = []

    i = 0
    if lines and _H1_RE.match(lines[0]):
        title = _H1_RE.match(lines[0]).group(1).strip()  # type: ignore[union-attr]
        i = 1
        while i < len(lines) and not lines[i].strip():
            i += 1

    intro: list[str] = []
    while i < len(lines):
        raw = lines[i]
        sm = _SUB_RE.match(raw)
        if sm:
            if intro and not sections:
                sections.append((title or _("Overview"), "\n".join(intro).strip()))
                intro = []
            flush()
            current = sm.group(1).strip()
            i += 1
            continue
        if not sections and not current:
            intro.append(raw)
        else:
            body.append(raw)
        i += 1
    if intro and not sections:
        sections.append((title or _("Overview"), "\n".join(intro).strip()))
    flush()
    return [(t, b) for t, b in sections if t.strip() or b.strip()]


@lru_cache(maxsize=256)
def _load_rule_readme(rule_id: str, lang: str) -> list[Section]:
    for path in _readme_candidates(rule_id, lang):
        if path.is_file():
            try:
                return _parse_readme(path.read_text(encoding="utf-8"))
            except OSError:
                continue
    return []


def _current_lang() -> str:
    for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        raw = os.environ.get(key) or ""
        if not raw:
            continue
        token = raw.split(":", 1)[0].strip()
        if token:
            return token.split(".", 1)[0]
    return "en"


def _ize_sections(code: str) -> list[Section]:
    targets = ize_targets_for_lint(code)
    cmd = ize_command_for_lint(code)
    if not targets:
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

    loc = lang if lang is not None else _current_lang()
    sections = list(_load_rule_readme(rule.id, loc))
    if not sections and rule.detail:
        sections = [(_("Detail"), rule.detail)]

    ize = _ize_sections(code)
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
    from std import IZE_RULES

    rule = LINT_RULES.by_id(rule_id) or LINT_RULES.lookup(code)
    if rule is None:
        rule = IZE_RULES.by_id(rule_id) or IZE_RULES.lookup(code)
    short = (rule.title if rule else code) or code
    return {
        "title": short,
        "sections": [{"title": t, "body": b} for t, b in d.sections],
    }


def clear_doc_cache() -> None:
    _load_rule_readme.cache_clear()
