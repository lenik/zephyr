# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read/write ``lint.comments`` (project + user) for browse / ``zfr comments``."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_COMMENTS_REL = Path(".config") / "zfr" / "lint.comments"

_SECTION_RE = re.compile(r"^\[([^\]]+)\]\s*$")
_ID_RE = re.compile(r"^(ZL|ZI|WL|WI)?(\d{1,4})$", re.I)


def user_comments_path() -> Path:
    return Path.home() / ".config" / "zfr" / "lint.comments"


def project_comments_path(root: Path) -> Path:
    return root / PROJECT_COMMENTS_REL


def normalize_rule_key(raw: str, *, default_prefix: str = "ZL") -> str:
    """Normalize ``ZL1`` / ``1`` / ``ZL0001`` → ``ZL0001``; ``NEW`` stays ``NEW``."""
    key = raw.strip()
    if not key:
        return key
    upper = key.upper()
    if upper in {"NEW", "REQUEST"}:
        return "NEW"
    m = _ID_RE.fullmatch(upper)
    if m:
        prefix = (m.group(1) or default_prefix).upper()
        return f"{prefix}{int(m.group(2)):04d}"
    return upper


def parse_comments(text: str, *, default_prefix: str = "ZL") -> dict[str, str]:
    """Parse ``[ZLxxxx]`` / ``[code]`` sections into rule-id → body."""
    out: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal current, buf
        if current is None:
            return
        body = "\n".join(buf).strip("\n")
        if body.strip():
            out[current] = body.strip() + "\n" if not body.endswith("\n") else body
        current = None
        buf = []

    for line in text.splitlines():
        m = _SECTION_RE.match(line.strip())
        if m:
            flush()
            current = normalize_rule_key(m.group(1), default_prefix=default_prefix)
            buf = []
            continue
        if current is not None:
            buf.append(line)
    flush()
    return out


def load_comments_file(path: Path, *, default_prefix: str = "ZL") -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        return parse_comments(path.read_text(encoding="utf-8"), default_prefix=default_prefix)
    except OSError:
        return {}


def format_comments(sections: dict[str, str]) -> str:
    lines: list[str] = []
    for key in sorted(
        sections,
        key=lambda k: (k in {"NEW", "REQUEST"}, not k.startswith(("ZL", "ZI", "WL", "WI")), k),
    ):
        body = sections[key].rstrip("\n")
        if not body.strip():
            continue
        lines.append(f"[{key}]")
        lines.append(body)
        lines.append("")
    return "\n".join(lines).rstrip() + ("\n" if lines else "")


def append_comment(
    path: Path,
    rule_key: str,
    text: str,
    *,
    default_prefix: str = "ZL",
) -> Path:
    """Append or merge a comment for *rule_key* into *path*."""
    key = normalize_rule_key(rule_key, default_prefix=default_prefix)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_comments_file(path, default_prefix=default_prefix)
    prev = existing.get(key, "").rstrip("\n")
    addition = text.strip("\n")
    if prev:
        existing[key] = prev + "\n\n" + addition + "\n"
    else:
        existing[key] = addition + "\n"
    path.write_text(format_comments(existing), encoding="utf-8")
    return path


def load_project_and_user_comments(
    root: Path,
    *,
    default_prefix: str = "ZL",
) -> tuple[dict[str, str], dict[str, str]]:
    return (
        load_comments_file(project_comments_path(root), default_prefix=default_prefix),
        load_comments_file(user_comments_path(), default_prefix=default_prefix),
    )


def comments_for_rule(root: Path, rule_id: str, *, default_prefix: str = "ZL") -> dict[str, str]:
    """Return ``project`` / ``user`` comment bodies for one rule."""
    rid = normalize_rule_key(rule_id, default_prefix=default_prefix)
    proj, user = load_project_and_user_comments(root, default_prefix=default_prefix)
    return {
        "project": proj.get(rid, ""),
        "user": user.get(rid, ""),
    }


def _filter_sections(
    sections: dict[str, str],
    rule_ids: set[str] | None,
    *,
    default_prefix: str = "ZL",
) -> dict[str, str]:
    if not rule_ids:
        return sections
    wanted = {normalize_rule_key(r, default_prefix=default_prefix) for r in rule_ids}
    return {k: v for k, v in sections.items() if k in wanted}


def delete_comments(
    root: Path,
    *,
    include_project: bool = True,
    include_user: bool = True,
    rule_ids: set[str] | None = None,
    default_prefix: str = "ZL",
) -> list[Path]:
    """Delete matching comment sections (or whole files when *rule_ids* is empty)."""
    touched: list[Path] = []
    targets: list[Path] = []
    if include_project:
        targets.append(project_comments_path(root))
    if include_user:
        targets.append(user_comments_path())
    for path in targets:
        if not path.is_file():
            continue
        if not rule_ids:
            path.unlink()
            touched.append(path)
            continue
        data = load_comments_file(path, default_prefix=default_prefix)
        wanted = {normalize_rule_key(r, default_prefix=default_prefix) for r in rule_ids}
        new = {k: v for k, v in data.items() if k not in wanted}
        if new == data:
            continue
        if new:
            path.write_text(format_comments(new), encoding="utf-8")
        else:
            path.unlink()
        touched.append(path)
    return touched


AI_HINT = (
    "AI hint: According to the project and user suggestions above, update the "
    "codebase and/or zfr tooling. When the work is finished, delete the consumed "
    "comments source file(s) "
    "(.config/zfr/lint.comments and/or ~/.config/zfr/lint.comments)."
)


def render_comments_report(
    root: Path,
    *,
    include_project: bool = True,
    include_user: bool = True,
    rule_ids: set[str] | None = None,
    default_prefix: str = "ZL",
    ai_hint: str | None = None,
) -> str:
    proj_path = project_comments_path(root)
    user_path = user_comments_path()
    parts: list[str] = []
    if include_project:
        proj = _filter_sections(
            load_comments_file(proj_path, default_prefix=default_prefix),
            rule_ids,
            default_prefix=default_prefix,
        )
        parts.append(f"# Project comments ({proj_path})")
        parts.append(format_comments(proj).rstrip() if proj else "(none)")
        parts.append("")
    if include_user:
        user = _filter_sections(
            load_comments_file(user_path, default_prefix=default_prefix),
            rule_ids,
            default_prefix=default_prefix,
        )
        parts.append(f"# User comments ({user_path})")
        parts.append(format_comments(user).rstrip() if user else "(none)")
        parts.append("")
    hint = AI_HINT if ai_hint is None else ai_hint
    if hint:
        parts.append(hint)
        parts.append("")
    return "\n".join(parts)
