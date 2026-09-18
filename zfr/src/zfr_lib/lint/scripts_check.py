# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lint: meson version subst, posync externalization, scripts/ layout."""

from __future__ import annotations

import re
from pathlib import Path

from ..i18n import _
from .finding import Finding
from .util import _read

# Maintenance / deploy run_targets that should call scripts/<name>.sh
_SCRIPT_TARGETS = (
    "posync",
    "look",
    "install-symlinks",
    "uninstall-symlinks",
    "deploy",
    "release-notes",
)

_ROOT_SCRIPT_NAMES = re.compile(
    r"^(install|deploy|build|ci|release|posync|look|maintain|bootstrap|setup)[-_].*\.sh$",
    re.I,
)

_VERSION_SUBST_RE = re.compile(
    r"""(?x)
    (?:
        \.set(?:_quoted)?\s*\(\s*['\"]VERSION['\"]
      | \.set(?:_quoted)?\s*\(\s*['\"]PROJECT_VERSION['\"]
      | set_quoted\s*\(\s*['\"]PROJECT_VERSION['\"]
      | set_quoted\s*\(\s*['\"]VERSION['\"]
    )
    """
)

_VERSION_USE_RE = re.compile(r"@VERSION@|\bPROJECT_VERSION\b")

_RUN_TARGET_RE = re.compile(
    r"run_target\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*command\s*:\s*\[(.*?)\]\s*,?\s*\)",
    re.S,
)


def meson_has_version_subst(meson_text: str) -> bool:
    return bool(_VERSION_SUBST_RE.search(meson_text))


def _iter_source_texts(root: Path) -> list[tuple[str, str]]:
    """Return (relpath, text) for candidate sources that may consume VERSION."""
    out: list[tuple[str, str]] = []
    skip = {
        ".git",
        "build",
        "debian",
        "packaging",
        "po",
        "man",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
    }
    suffixes = {
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cc",
        ".hh",
        ".py",
        ".sh",
        ".bash",
        ".pl",
        ".rb",
        ".rs",
        ".go",
        ".js",
        ".ts",
    }

    def consider(path: Path) -> None:
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            return
        if any(p in skip for p in Path(rel).parts):
            return
        if path.suffix.lower() not in suffixes and not path.name.endswith(".in"):
            return
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return
        out.append((rel, text))

    src = root / "src"
    if src.is_dir():
        for path in src.rglob("*"):
            if path.is_file():
                consider(path)
    # configure_file inputs / wrappers at project root
    for path in root.iterdir():
        if path.is_file():
            consider(path)
    scripts = root / "scripts"
    if scripts.is_dir():
        for path in scripts.rglob("*"):
            if path.is_file():
                consider(path)
    return out


def sources_use_version(root: Path) -> list[str]:
    hits: list[str] = []
    seen: set[str] = set()
    for rel, text in _iter_source_texts(root):
        if rel in seen:
            continue
        seen.add(rel)
        if _VERSION_USE_RE.search(text):
            hits.append(rel)
    return hits


def _run_target_blocks(meson_text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _RUN_TARGET_RE.finditer(meson_text)]


def _command_uses_scripts(command: str, name: str) -> bool:
    """True when the run_target command references scripts/<name>.sh (or .bash)."""
    needle = f"scripts/{name}"
    if needle in command.replace("\\", "/"):
        return True
    # Meson path join forms: 'scripts' / 'posync.sh'
    if re.search(
        rf"['\"]scripts['\"]\s*/\s*['\"]{re.escape(name)}\.(?:sh|bash)['\"]",
        command,
    ):
        return True
    return False


def _command_is_inline_script(command: str) -> bool:
    """True when command embeds a multi-line bash -euc / -c body."""
    if "'''" in command or '"""' in command:
        return True
    if re.search(r"bash['\"]?\s*,\s*['\"]-[^'\"]*c", command):
        # Single-line -c with substantial body
        if len(command) > 120:
            return True
    return False


def check_version_subst(root: Path, role: str) -> list[Finding]:
    if role in {"meta"}:
        return []
    meson = root / "meson.build"
    if not meson.is_file():
        return []
    text = _read(meson)
    has_subst = meson_has_version_subst(text)
    used = sources_use_version(root)
    rel = "meson.build"
    if has_subst and used:
        return [
            Finding(
                "ok",
                "meson.version_subst",
                _("VERSION/PROJECT_VERSION substituted and used in %s") % used[0],
                rel,
            )
        ]
    if has_subst and not used:
        return [
            Finding(
                "warn",
                "meson.version_subst",
                _("meson configures VERSION/PROJECT_VERSION but no source uses it"),
                rel,
                fix=_(
                    "Reference @VERSION@ (scripts → *.in + configure_file) or "
                    "PROJECT_VERSION from config.h in at least one source. "
                    "Or run `zfr ize`."
                ),
            )
        ]
    if used and not has_subst:
        return [
            Finding(
                "warn",
                "meson.version_subst",
                _("sources use @VERSION@/PROJECT_VERSION but meson does not substitute it"),
                used[0],
                fix=_(
                    "Add configuration_data set('VERSION', …) / set_quoted('PROJECT_VERSION', …) "
                    "and configure_file. Or run `zfr ize`."
                ),
            )
        ]
    # Neither: note for apps that should wire version display.
    if role == "app":
        return [
            Finding(
                "note",
                "meson.version_subst",
                _("no Meson VERSION/PROJECT_VERSION substitution found"),
                rel,
                fix=_(
                    "Wire meson configuration_data for VERSION and use it in a source. "
                    "Or run `zfr ize`."
                ),
            )
        ]
    return []


def check_posync(root: Path, role: str) -> list[Finding]:
    if role in {"meta"}:
        return []
    po = root / "po"
    meson = root / "meson.build"
    if not po.is_dir() or not meson.is_file():
        return []
    text = _read(meson)
    blocks = {name: body for name, body in _run_target_blocks(text)}
    if "posync" not in blocks:
        return [
            Finding(
                "note",
                "layout.posync",
                _("po/ present but no run_target('posync')"),
                "meson.build",
                fix=_("Add run_target posync calling scripts/posync.sh. Or run `zfr ize`."),
            )
        ]
    body = blocks["posync"]
    script = root / "scripts" / "posync.sh"
    if _command_uses_scripts(body, "posync") and script.is_file():
        return [
            Finding(
                "ok",
                "layout.posync",
                _("posync externalized as scripts/posync.sh"),
                "scripts/posync.sh",
            )
        ]
    if script.is_file() and not _command_uses_scripts(body, "posync"):
        return [
            Finding(
                "warn",
                "layout.posync",
                _("scripts/posync.sh exists but meson posync does not call it"),
                "meson.build",
                fix=_("Point run_target('posync') at scripts/posync.sh. Or run `zfr ize`."),
            )
        ]
    return [
        Finding(
            "warn",
            "layout.posync",
            _("posync is inline in meson.build; externalize to scripts/posync.sh"),
            "meson.build",
            fix=_("Extract the posync body to scripts/posync.sh and call it from "
            "run_target. Or run `zfr ize`."),
        )
    ]


def check_scripts_layout(root: Path, role: str) -> list[Finding]:
    if role in {"meta"}:
        return []
    out: list[Finding] = []
    # Root-level maintenance shells
    for path in sorted(root.glob("*.sh")):
        name = path.name
        if name.endswith(".bash"):
            continue
        if _ROOT_SCRIPT_NAMES.match(name) or name in {
            "posync.sh",
            "look.sh",
            "install-symlinks.sh",
            "uninstall-symlinks.sh",
            "deploy.sh",
        }:
            out.append(
                Finding(
                    "warn",
                    "layout.scripts",
                    _("maintenance script %s should live under scripts/") % name,
                    name,
                    fix=_("Move to scripts/%s and update callers. Or run `zfr ize`.") % name,
                )
            )

    meson = root / "meson.build"
    if meson.is_file():
        text = _read(meson)
        for name, body in _run_target_blocks(text):
            if name not in _SCRIPT_TARGETS:
                continue
            if _command_uses_scripts(body, name):
                continue
            if not _command_is_inline_script(body):
                continue
            # posync also reported by check_posync; still list under layout.scripts
            # when other targets are inline — skip duplicate for posync alone.
            if name == "posync":
                continue
            out.append(
                Finding(
                    "warn",
                    "layout.scripts",
                    _("run_target('%s') should call scripts/%s.sh") % (name, name),
                    "meson.build",
                    fix=_(
                        "Extract the inline script to scripts/%s.sh and reference it "
                        "from meson. Or run `zfr ize`."
                    )
                    % name,
                )
            )

    if not out:
        scripts = root / "scripts"
        if scripts.is_dir() or not (root / "meson.build").is_file():
            out.append(
                Finding(
                    "ok",
                    "layout.scripts",
                    _("build/deploy/maintenance scripts under scripts/ (or none)"),
                )
            )
    return out


def check_scripts_and_version(root: Path, role: str) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_version_subst(root, role))
    findings.extend(check_posync(root, role))
    findings.extend(check_scripts_layout(root, role))
    return findings
