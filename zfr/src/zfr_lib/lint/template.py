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
        ".vscode",
    }
    name = _project_name(root)
    missing: list[str] = []
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
        if expected.parts[0] in {"debian", "docs", "src", "tests", "packaging", ".githooks"} or expected.name in {
            "meson.build",
            "LICENSE",
            "README.md",
            "README-zh.md",
            "VERSION",
        }:
            missing.append(expected.as_posix())
    if not missing:
        return [Finding("ok", "template.coverage", _("structural files from the language template are present"))]
    preview = ", ".join(missing[:12])
    more = "" if len(missing) <= 12 else _(" (+%d more)") % (len(missing) - 12)
    return [
        Finding(
            "note",
            "template.coverage",
            _("language template %(lang)s has extra scaffolding not in this tree: %(preview)s%(more)s")
            % {"lang": lang, "preview": preview, "more": more},
            fix=_("Compare with the %(lang)s template under pkgdatadir. Copy missing debian/docs/src/packaging "
            "files (packaging/rpm/ uses %(name)s.spec, not zephyr.spec; "
            "debian/%(name)s.substvars not zephyr.substvars), or `zfr add` puffs. "
            "Do not copy build/ or debian leftover stamp files. "
            "Example commons modules are optional.") % {"lang": lang, "name": name},
        )
    ]
