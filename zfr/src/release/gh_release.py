# SPDX-License-Identifier: AGPL-3.0-or-later
"""GitHub release notes and gh release create."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .logutil import log1, run

from .artifacts import step_collect_artifacts
from .context import Context

_HEADER_RE = re.compile(
    r"^(\S+)\s+\(([^)]+)\)\s+([^;]+);\s*urgency=(\S+)",
)
_TRAILER_RE = re.compile(r"^  -- ")


@dataclass(frozen=True)
class ChangelogStanza:
    package: str
    version: str
    distribution: str
    urgency: str
    bullets: tuple[str, ...]


def normalize_release_version(version: str) -> str:
    """Strip epoch, Debian revision, and leading ``v`` for comparisons."""
    v = (version or "").strip()
    if ":" in v:
        v = v.split(":", 1)[1]
    if "-" in v:
        # Keep upstream part only (2.9.0-1 → 2.9.0).
        v = v.split("-", 1)[0]
    return v.lstrip("vV")


def parse_debian_changelog(text: str) -> list[ChangelogStanza]:
    """Parse debian/changelog into newest-first stanzas (bullets only)."""
    stanzas: list[ChangelogStanza] = []
    package = version = distribution = urgency = ""
    bullets: list[str] = []
    in_entry = False

    def flush() -> None:
        nonlocal in_entry, bullets, package, version, distribution, urgency
        if not in_entry or not version:
            bullets = []
            in_entry = False
            return
        stanzas.append(
            ChangelogStanza(
                package=package,
                version=version,
                distribution=distribution,
                urgency=urgency,
                bullets=tuple(bullets),
            )
        )
        bullets = []
        in_entry = False

    for line in text.splitlines():
        hm = _HEADER_RE.match(line)
        if hm:
            flush()
            package = hm.group(1)
            version = hm.group(2).strip()
            distribution = hm.group(3).strip()
            urgency = hm.group(4).rstrip(".").strip()
            in_entry = True
            continue
        if not in_entry:
            continue
        if _TRAILER_RE.match(line):
            flush()
            continue
        if line.startswith("  * "):
            bullets.append(line[4:].rstrip())
        elif line.startswith("    ") and bullets:
            # Continuation of previous bullet.
            bullets[-1] = (bullets[-1] + " " + line.strip()).strip()
    flush()
    return stanzas


def last_github_release_version(
    *, cwd: Path | str | None = None
) -> str | None:
    """Return the newest GitHub release tag's version, or None."""
    try:
        proc = subprocess.run(
            ["gh", "release", "list", "-L", "1", "--json", "tagName"],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        rows = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list) or not rows:
        return None
    tag = str(rows[0].get("tagName") or "").strip()
    return normalize_release_version(tag) or None


def stanzas_since_last_release(
    stanzas: list[ChangelogStanza],
    *,
    current_version: str,
    since_version: str | None,
) -> list[ChangelogStanza]:
    """Newest-first stanzas from *current* down to (excluding) *since_version*.

    When *since_version* is None (no prior GitHub release), return only the
    current stanza.
    """
    current = normalize_release_version(current_version)
    since = normalize_release_version(since_version) if since_version else None
    if since is None:
        for stanza in stanzas:
            if normalize_release_version(stanza.version) == current:
                return [stanza]
        return [stanzas[0]] if stanzas else []

    out: list[ChangelogStanza] = []
    started = False
    for stanza in stanzas:
        ver = normalize_release_version(stanza.version)
        if not started:
            if ver != current:
                continue
            started = True
        if ver == since:
            break
        out.append(stanza)
    if not out and stanzas:
        for stanza in stanzas:
            if normalize_release_version(stanza.version) == current:
                return [stanza]
        return [stanzas[0]]
    return out


def format_release_notes(stanzas: list[ChangelogStanza]) -> str:
    """Format aggregated notes (Release + Internal Version sections)."""
    if not stanzas:
        return "See README.md and debian/changelog.\n"
    parts: list[str] = []
    for i, stanza in enumerate(stanzas):
        ver = normalize_release_version(stanza.version)
        heading = f"Release {ver}" if i == 0 else f"Internal Version {ver}"
        parts.append(heading)
        parts.append("")
        if stanza.bullets:
            for b in stanza.bullets:
                parts.append(f"- {b}")
            parts.append("")
    parts.append("See README.md and debian/changelog.")
    parts.append("")
    return "\n".join(parts)


def get_release_notes(
    project_type: str,
    projectdir: Path | str,
    version: str,
) -> str:
    """Write release notes to a temp file; return its path."""
    projectdir = Path(projectdir)
    fd, notes_path = tempfile.mkstemp(prefix="zfr-release-notes-", text=True)
    with open(fd, "w", encoding="utf-8") as notes:
        if project_type == "debian":
            changelog = projectdir / "debian" / "changelog"
            text = changelog.read_text(encoding="utf-8") if changelog.is_file() else ""
            stanzas = parse_debian_changelog(text)
            since = last_github_release_version(cwd=projectdir)
            if since:
                log1(f"Aggregating changelog since GitHub release {since}")
            else:
                log1("No prior GitHub release found; using current changelog stanza")
            selected = stanzas_since_last_release(
                stanzas, current_version=version, since_version=since
            )
            notes.write(format_release_notes(selected))
        elif project_type in ("vsix", "nodejs"):
            log1("Getting release notes from recent commit")
            notes.write(f"Release {version}\n\n")
            body = subprocess.check_output(
                ["git", "log", "-1", "--format=%B"],
                text=True,
            )
            notes.write(body)
            if not body.endswith("\n"):
                notes.write("\n")
            notes.write("\n")

    return notes_path


def step_gh_release(ctx: Context) -> None:
    if ctx.opts.local or ctx.opts.no_release:
        if ctx.opts.no_release and not ctx.opts.local:
            log1("Skipping GitHub release (--no-release)")
        return

    step_collect_artifacts(ctx)

    ctx.notes = get_release_notes(
        ctx.project_type, ctx.projectdir, ctx.version
    )
    try:
        log1(f"Creating GitHub release {ctx.tag}")
        run(
            "gh",
            "release",
            "create",
            ctx.tag,
            ctx.tarball,
            *ctx.attachments,
            "--title",
            ctx.tag,
            "--notes-file",
            ctx.notes,
        )
        print(f"Created release {ctx.tag}")
    finally:
        try:
            Path(ctx.notes).unlink(missing_ok=True)
        except OSError:
            pass
