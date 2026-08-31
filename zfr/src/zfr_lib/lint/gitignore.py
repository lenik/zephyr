# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lint .gitignore coverage for root and component subdirectories."""

from __future__ import annotations

from pathlib import Path

from ..i18n import _
from .finding import Finding

# Patterns every JS/TS or multi-package tree should ignore at the project root.
_ROOT_COMMON = (
    "node_modules/",
    "dist/",
)

# Extra common build/cache noise (note-level if missing when root check applies).
_ROOT_EXTRA = (
    "__pycache__/",
    "build/",
    ".cache/",
)

# When these directories exist, expect a nested .gitignore with the listed patterns.
_COMPONENT_REQUIRED: dict[str, tuple[str, ...]] = {
    "backend": ("src/generated/", "node_modules/", "dist/"),
    "web": ("node_modules/", "dist/"),
    "frontend": ("node_modules/", "dist/"),
    "mobile": ("node_modules/", "dist/"),
    "prisma": ("node_modules/",),
    "e2e": ("node_modules/", "test-results/", "playwright-report/"),
}


def _gitignore_lines(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def _covers(lines: list[str], pattern: str) -> bool:
    """True if *pattern* is present (exact, trailing-slash variants, or **/form)."""
    variants = {pattern, pattern.rstrip("/"), pattern.rstrip("/") + "/"}
    alt = pattern.lstrip("./")
    variants.update({alt, alt.rstrip("/"), alt.rstrip("/") + "/"})
    variants.add("**/" + alt.lstrip("/"))
    variants.add("**/" + alt.rstrip("/") + "/")
    for line in lines:
        if line in variants:
            return True
        # Allow ``backend/src/generated/`` style when checking ``src/generated/``
        # only inside a component file — callers pass component-local lines.
        if line.endswith("/" + pattern) or line.endswith("/" + pattern.rstrip("/")):
            return True
    return False


def _needs_js_style_root(root: Path) -> bool:
    if (root / "package.json").is_file():
        return True
    if (root / "pnpm-workspace.yaml").is_file() or (root / "pnpm-lock.yaml").is_file():
        return True
    if (root / "yarn.lock").is_file() or (root / "package-lock.json").is_file():
        return True
    for name in _COMPONENT_REQUIRED:
        if (root / name).is_dir():
            return True
    return False


def check_gitignore(root: Path, role: str) -> list[Finding]:
    """Validate root and component ``.gitignore`` files when applicable."""
    if role == "meta":
        return []

    out: list[Finding] = []
    gi = root / ".gitignore"
    js_root = _needs_js_style_root(root)

    if not gi.is_file():
        if js_root:
            out.append(
                Finding(
                    "warn",
                    "layout.gitignore",
                    _("missing root .gitignore"),
                    ".gitignore",
                    fix=_(
                        "Add a root .gitignore covering node_modules/, dist/, "
                        "and other build artifacts. Component dirs (backend/, web/, …) "
                        "should get their own .gitignore too."
                    ),
                )
            )
        # Non-JS trees often inherit ignores from a parent meta-repo; stay quiet.
        root_lines: list[str] = []
    else:
        root_lines = _gitignore_lines(gi)
        out.append(Finding("ok", "layout.gitignore", _("root .gitignore present"), ".gitignore"))

    if js_root and gi.is_file():
        missing = [p for p in _ROOT_COMMON if not _covers(root_lines, p)]
        if missing:
            out.append(
                Finding(
                    "warn",
                    "layout.gitignore.common",
                    _("root .gitignore missing common patterns: %s") % ", ".join(missing),
                    ".gitignore",
                    fix=_("Add %s to the project-root .gitignore.") % ", ".join(missing),
                )
            )
        else:
            out.append(
                Finding(
                    "ok",
                    "layout.gitignore.common",
                    _("root .gitignore covers node_modules/ and dist/"),
                    ".gitignore",
                )
            )
        extra_missing = [p for p in _ROOT_EXTRA if not _covers(root_lines, p)]
        if extra_missing:
            out.append(
                Finding(
                    "note",
                    "layout.gitignore.extra",
                    _("root .gitignore could also ignore: %s") % ", ".join(extra_missing),
                    ".gitignore",
                )
            )

    for comp, required in sorted(_COMPONENT_REQUIRED.items()):
        comp_dir = root / comp
        if not comp_dir.is_dir():
            continue
        cgi = comp_dir / ".gitignore"
        code = f"layout.gitignore.{comp}"
        rel = f"{comp}/.gitignore"
        if not cgi.is_file():
            out.append(
                Finding(
                    "warn",
                    code,
                    _("missing %s (component directory exists)") % rel,
                    rel,
                    fix=_("Add %s covering: %s") % (rel, ", ".join(required)),
                )
            )
            continue
        lines = _gitignore_lines(cgi)
        missing = [p for p in required if not _covers(lines, p)]
        if missing:
            out.append(
                Finding(
                    "warn",
                    code,
                    _("%s missing patterns: %s") % (rel, ", ".join(missing)),
                    rel,
                    fix=_("Add to %s: %s") % (rel, ", ".join(missing)),
                )
            )
        else:
            out.append(
                Finding(
                    "ok",
                    code,
                    _("%s covers required patterns") % rel,
                    rel,
                )
            )

    return out
