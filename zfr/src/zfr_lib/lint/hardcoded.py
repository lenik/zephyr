# SPDX-License-Identifier: AGPL-3.0-or-later
"""Detect hardcoded install paths and version strings in sources."""

from __future__ import annotations

import re
from pathlib import Path

from .. import (
    changelog_version,
    is_probably_text,
    iter_files,
    version_file_version,
    _is_zfr_cli_package,
)
from ..i18n import _
from .finding import Finding
from .util import _rel

# Absolute FHS-style install paths (not shebangs). Longest matches preferred later.
_ABS_PATH_RE = re.compile(
    r"(?<![/\w])(/usr(?:/local)?(?:/(?:share|libexec|lib|bin|sbin|include|etc)"
    r"(?:/[^/\s'\"`]+)*)?|/opt/[^/\s'\"`]+(?:/[^/\s'\"`]+)*)"
)

_SKIP_PREFIXES = (
    "debian/",
    "packaging/",
    "po/",
    "docs/",
    "build/",
    ".git/",
    "tests/",
)

_SKIP_NAMES = {
    "meson.build",
    "meson_options.txt",
    "CMakeLists.txt",
    "configure.ac",
    "Makefile",
    "Makefile.am",
}

_SCRIPT_SUFFIXES = {".sh", ".bash", ".py", ".pl", ".rb", ".js", ".ts"}


def _project_version_tokens(root: Path) -> set[str]:
    ver = changelog_version(root) or version_file_version(root)
    if not ver or ver in {"0.0.0", "0"}:
        return set()
    tokens = {ver, ver.lstrip("v")}
    if ver.startswith("v"):
        tokens.add(ver[1:])
    # Ignore very short tokens (too many false positives).
    return {t for t in tokens if t and len(t) >= 3 and re.search(r"\d", t)}


def _is_installable_script(root: Path, path: Path) -> bool:
    """True for scripts that should use configure_file placeholders (not libraries)."""
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return False
    parts = Path(rel).parts
    # Skip Python/C packages and deep library trees.
    if any(p.endswith("_lib") or p == "lib" for p in parts[:-1]):
        return False
    if path.suffix in {".c", ".h", ".cpp", ".hpp", ".cc", ".hh"}:
        # C/C++ version literals are handled; paths rarely belong in sources.
        return True
    if path.suffix.lower() not in _SCRIPT_SUFFIXES and path.suffix:
        return False
    # Top-level src/foo.py or src/foo.sh (not src/pkg/module.py).
    if rel.startswith("src/"):
        rest = parts[1:]
        if len(rest) == 1:
            return True
        return False
    if rel.startswith(("tools/", "completions/", "apps/")):
        return True
    if len(parts) == 1 and path.suffix.lower() in _SCRIPT_SUFFIXES:
        return True
    return False


def _is_candidate(root: Path, path: Path) -> bool:
    if not path.is_file() or not is_probably_text(path):
        return False
    if path.name.endswith(".in") or path.suffix == ".in":
        return False
    if path.name in _SKIP_NAMES:
        return False
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return False
    if any(rel.startswith(p) for p in _SKIP_PREFIXES):
        return False
    return _is_installable_script(root, path)

def _line_is_shebang(line: str) -> bool:
    return line.lstrip().startswith("#!")


def _version_hits(text: str, tokens: set[str]) -> list[tuple[int, str]]:
    """Return (lineno, token) for string-ish version literals."""
    hits: list[tuple[int, str]] = []
    if not tokens:
        return hits
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            continue
        for tok in sorted(tokens, key=len, reverse=True):
            # Quoted or simple assignment / echo contexts.
            if re.search(
                rf"""(?x)
                (?:
                    ['"]{re.escape(tok)}['"]
                    | \bVERSION\s*=\s*['"]?{re.escape(tok)}['"]?
                    | \bversion\s*[:=]\s*['"]{re.escape(tok)}['"]
                )
                """,
                line,
            ):
                hits.append((i, tok))
                break
    return hits


def _path_hits(text: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        if _line_is_shebang(line):
            continue
        # Skip commented-out examples.
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        for m in _ABS_PATH_RE.finditer(line):
            path = m.group(1)
            if path in {"/usr", "/usr/local"}:
                if "prefix" not in line.lower() and "PREFIX" not in line:
                    continue
            hits.append((i, path))
    return hits


def check_hardcoded(root: Path, role: str) -> list[Finding]:
    """Warn about hardcoded FHS paths and project version strings in scripts."""
    if role in {"meta"}:
        return []
    if _is_zfr_cli_package(root):
        # zfr itself uses .in wrappers; library code probes /usr by design.
        return [
            Finding(
                "ok",
                "source.hardcoded",
                _("zfr CLI package uses configure_file wrappers for install paths"),
            )
        ]
    out: list[Finding] = []
    tokens = _project_version_tokens(root)
    path_files: list[str] = []
    ver_files: list[str] = []
    for path in iter_files(root):
        if not _is_candidate(root, path):
            continue
        # C/C++: only check version literals (paths stay as lint-optional).
        c_family = path.suffix in {".c", ".h", ".cpp", ".hpp", ".cc", ".hh"}
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = _rel(root, path)
        has_path_ph = bool(
            re.search(
                r"@(?:PREFIX|DATADIR|BINDIR|LIBDIR|LIBEXECDIR|SBINDIR|LOCALEDIR|PKGDATADIR)@",
                text,
            )
        )
        has_ver_ph = "@VERSION@" in text or "PROJECT_VERSION" in text

        if not c_family:
            paths = _path_hits(text)
            if paths and not has_path_ph:
                line, sample = paths[0]
                more = len(paths) - 1
                msg = _("hardcoded install path %(sample)s in %(rel)s") % {
                    "sample": sample,
                    "rel": rel,
                }
                if more:
                    msg += _(" (+%d more)") % more
                out.append(
                    Finding(
                        "warn",
                        "source.hardcoded.path",
                        msg,
                        rel,
                        line=line,
                        fix=_(
                            "Replace with meson configure_file placeholders "
                            "(@PREFIX@, @DATADIR@, @BINDIR@, @LIBDIR@, @LOCALEDIR@, "
                            "@PKGDATADIR@): rename to *.in and run `zfr ize`."
                        ),
                    )
                )
                path_files.append(rel)
        versions = _version_hits(text, tokens)
        if versions and not has_ver_ph:
            line, sample = versions[0]
            out.append(
                Finding(
                    "warn",
                    "source.hardcoded.version",
                    _("hardcoded version %(sample)s in %(rel)s")
                    % {"sample": sample, "rel": rel},
                    rel,
                    line=line,
                    fix=_(
                        "Use @VERSION@ (scripts → *.in + configure_file) or "
                        "PROJECT_VERSION from config.h (C/C++). Run `zfr ize`."
                    ),
                )
            )
            ver_files.append(rel)

    if not path_files and not ver_files:
        out.append(
            Finding(
                "ok",
                "source.hardcoded",
                _("no hardcoded install paths or project version strings in sources"),
            )
        )
    return out
