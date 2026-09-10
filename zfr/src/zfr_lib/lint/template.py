# SPDX-License-Identifier: AGPL-3.0-or-later
"""Template-gap checks."""

from __future__ import annotations

from pathlib import Path

from .. import (
    LANGS,
    TEMPLATE_PUFF,
    _is_zfr_cli_package,
    iter_files,
    template_dir,
)
from ..i18n import _
from ..packaging import _meson_project_fields
from .finding import Finding
from .util import _control, is_example_shared_rel

# Non-rpm packaging trees and convenience src files are optional scaffolding.
_OPTIONAL_PREFIXES: tuple[str, ...] = (
    "packaging/arch/",
    "packaging/freebsd/",
    "packaging/macos/",
    "packaging/win32/",
    "packaging/lib/",
)

_OPTIONAL_EXACT: frozenset[str] = frozenset(
    {
        "packaging/README.md",
        "src/Makefile",
    }
)

# Per-language optional src helpers shipped by templates but not required.
_OPTIONAL_BY_LANG: dict[str, frozenset[str]] = {
    "clib": frozenset(
        {
            "src/Makefile",
            "src/bulk.h",
            "src/c_pch.h",
            "src/lib.c",
            "src/lib.h",
        }
    ),
    "cpplib": frozenset(
        {
            "src/Makefile",
            "src/bulk.hpp",
            "src/cpp_pch.hpp",
            "src/lib.cpp",
            "src/lib.hpp",
        }
    ),
    "typescript": frozenset(
        {
            "src/i18n.ts",
        }
    ),
}


def _project_name(root: Path) -> str:
    src, _pkg, _ctl = _control(root)
    meson = _meson_project_fields(root)
    return src.get("Source") or meson.get("name") or root.name


def _expected_rel(rel: Path, project_name: str) -> Path:
    """Map template paths that use the zephyr placeholder to the instance name.

    Templates ship ``packaging/rpm/zephyr.spec`` and ``debian/zephyr.substvars``;
    instantiated projects use ``<project>.spec`` / ``<project>.substvars``.
    """
    parts = list(rel.parts)
    if not parts:
        return rel
    name = parts[-1]
    if name == "zephyr.spec":
        parts[-1] = f"{project_name}.spec"
        return Path(*parts)
    if name == "zephyr.substvars":
        parts[-1] = f"{project_name}.substvars"
        return Path(*parts)
    return rel


def is_optional_scaffold(rel_posix: str, lang: str) -> bool:
    """True when a template-relative path is optional (not required to match)."""
    if rel_posix in _OPTIONAL_EXACT:
        return True
    if any(rel_posix.startswith(prefix) for prefix in _OPTIONAL_PREFIXES):
        return True
    name = Path(rel_posix).name
    if name.endswith(".example"):
        return True
    lang_opts = _OPTIONAL_BY_LANG.get(lang)
    if lang_opts and rel_posix in lang_opts:
        return True
    return False


def _is_noise_scaffold(rel_posix: str) -> bool:
    """VCS / editor noise that should not appear in coverage reports."""
    name = Path(rel_posix).name
    return name in {".gitignore", ".gitattributes", ".DS_Store"}


# debian/ leftovers that may appear under language templates but are not scaffolding.
_DEBIAN_TMPL_SKIP = frozenset(
    {
        "debhelper-build-stamp",
        "files",
        "substvars",  # unprefixed leftover
    }
)


def check_template_gaps(root: Path, lang: str, role: str) -> list[Finding]:
    """Warn about structural files the language template has that this tree lacks."""
    if role == "meta" or lang not in LANGS:
        return []
    if _is_zfr_cli_package(root):
        return [
            Finding(
                "ok",
                "template.coverage",
                _("zfr CLI package is not a language template"),
            )
        ]
    try:
        tmpl = template_dir(lang)
    except SystemExit:
        return []
    if tmpl.resolve() == root.resolve():
        return []
    skip_top = {
        "build",
        "rpmbuild",
        ".git",
        "CLAUDE.md",
        ".cursor",
        ".githooks",
        ".vscode",
    }
    name = _project_name(root)
    required_missing: list[str] = []
    optional_missing: list[str] = []
    for path in iter_files(tmpl):
        rel = path.relative_to(tmpl)
        if rel.parts and rel.parts[0] in skip_top:
            continue
        if TEMPLATE_PUFF in path.name or TEMPLATE_PUFF in rel.as_posix():
            continue
        # Example shared helpers (commons / common_lib) and their unit tests
        # are template demos, not required project scaffolding.
        if is_example_shared_rel(rel):
            continue
        if (
            rel.parts
            and rel.parts[0] == "debian"
            and (
                rel.name in _DEBIAN_TMPL_SKIP
                or rel.name.endswith(".debhelper")
                or rel.name.endswith(".debhelper.log")
                or rel.name.endswith(".buildinfo")
            )
        ):
            continue
        expected = _expected_rel(rel, name)
        if (root / expected).exists():
            continue
        # only flag well-known scaffolding, not every po locale
        top = expected.parts[0] if expected.parts else ""
        root_names = {"meson.build", "README.md", "README-zh_CN.md", "VERSION"}
        if top in {"debian", "docs", "src", "tests", "packaging"} or (
            len(expected.parts) == 1 and expected.name in root_names
        ):
            rel_s = expected.as_posix()
            if _is_noise_scaffold(rel_s):
                continue
            if is_optional_scaffold(rel_s, lang):
                optional_missing.append(rel_s)
            else:
                required_missing.append(rel_s)

    if not required_missing and not optional_missing:
        return [Finding("ok", "template.coverage", _("structural files from the language template are present"))]

    # Only optional gaps: informational, not a real coverage problem.
    if not required_missing:
        preview = ", ".join(f"{p} [optional]" for p in optional_missing[:12])
        more = "" if len(optional_missing) <= 12 else _(" (+%d more)") % (len(optional_missing) - 12)
        return [
            Finding(
                "ok",
                "template.coverage",
                _("language template %(lang)s optional scaffolding not in this tree: %(preview)s%(more)s")
                % {"lang": lang, "preview": preview, "more": more},
                fix=_("Optional only (safe to omit): non-rpm packaging/*, src/Makefile, "
                "and language helpers such as clib src/{bulk.h,c_pch.h,lib.c,lib.h}. "
                "Do not copy build/ or debian leftover stamp files."),
            )
        ]

    # Required gaps drive the note; optional listed separately (not mixed into preview).
    preview = ", ".join(f"{p} [required]" for p in required_missing[:12])
    more = "" if len(required_missing) <= 12 else _(" (+%d more)") % (len(required_missing) - 12)
    opt_note = ""
    if optional_missing:
        opt_bits = [f"{p} [optional]" for p in optional_missing[:8]]
        opt_note = _(" Also absent (optional, not required): %(opts)s.") % {
            "opts": ", ".join(opt_bits)
            + ("" if len(optional_missing) <= 8 else _(" (+%d more)") % (len(optional_missing) - 8))
        }
    return [
        Finding(
            "note",
            "template.coverage",
            _("language template %(lang)s has extra scaffolding not in this tree: %(preview)s%(more)s")
            % {"lang": lang, "preview": preview, "more": more}
            + opt_note,
            fix=_("Compare with the %(lang)s template under pkgdatadir. Copy missing "
            "[required] debian/docs/src/tests/packaging/rpm files "
            "(packaging/rpm/ uses %(name)s.spec, not zephyr.spec; "
            "debian/%(name)s.substvars not zephyr.substvars), or `zfr add` puffs. "
            "[optional] items (non-rpm packaging/*, src/Makefile, clib/cpplib "
            "bulk/pch/lib helpers, …) may be omitted. "
            "Do not copy build/ or debian leftover stamp files. "
            "Example commons modules are optional.") % {"lang": lang, "name": name},
        )
    ]
