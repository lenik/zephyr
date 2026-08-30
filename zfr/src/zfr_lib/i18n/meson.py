# SPDX-License-Identifier: AGPL-3.0-or-later
"""Meson po/meson.build hooks for build-time derived locale generation."""

from __future__ import annotations

import re
from pathlib import Path

_MARKER_BEGIN = "# zfr: i18n-derive-begin"

_DERIVE_BLOCK = """\
# zfr: i18n-derive-begin
_po_src = meson.current_source_dir()
_po_build = meson.current_build_dir()
_sh = find_program('sh')
_po_dep_list = run_command(
  _sh, '-c', 'cd "$1" && ls -1 *.po LINGUAS 2>/dev/null || true',
  _po_src, check: false,
).stdout().strip().split('\\n')
_po_dep_files = []
foreach _p : _po_dep_list
  if _p != ''
    _po_dep_files += [_p]
  endif
endforeach

_zfr_i18n = find_program('zfr', native: true, required: false)
if _zfr_i18n.found()
  custom_target(
    'i18n-derive',
    command: [
      _zfr_i18n, 'i18n', '-b',
      '--po-dir', _po_build,
      '--stamp', '@OUTPUT@',
      '--compile-mo',
      '--domain', 'zfr',
    ],
    output: 'i18n-derive.stamp',
    depend_files: _po_dep_files,
    build_by_default: true,
    console: true,
  )
endif
# zfr: i18n-derive-end
"""

_DOMAIN_RE = re.compile(
    r"i18n\.gettext\s*\(\s*['\"](?P<domain>[^'\"]+)['\"]",
    re.MULTILINE,
)


def _patch_existing(text: str) -> str:
    if _MARKER_BEGIN in text:
        return text
    domain = "zfr"
    match = _DOMAIN_RE.search(text)
    if match:
        domain = match.group("domain")

    if "i18n = import('i18n')" in text:
        text = text.replace(
            "i18n = import('i18n')",
            "i18n = import('i18n')\n\n" + _DERIVE_BLOCK,
            1,
        )
    else:
        text = "i18n = import('i18n')\n\n" + _DERIVE_BLOCK + "\n" + text

    text = re.sub(
        r"data_dirs\s*:\s*\[[^\]]+\]",
        "data_dirs: _po_src",
        text,
        count=1,
    )
    text = re.sub(
        r"data_dirs\s*:\s*[^\n,]+",
        "data_dirs: _po_src",
        text,
        count=1,
    )
    if "_i18n_targets = i18n.gettext" in text:
        text = re.sub(
            r"_i18n_targets = i18n\.gettext\(",
            "i18n.gettext(",
            text,
            count=1,
        )
    text = re.sub(
        r"(?m)^if _zfr_i18n\.found\(\)\s*\n\s*foreach.*?\n\s*endforeach\s*\n\s*endif\s*\n",
        "",
        text,
        count=1,
        flags=re.DOTALL,
    )
    return text


def ensure_po_meson_derive(root: Path, *, dry_run: bool = False) -> list[str]:
    """Patch ``po/meson.build`` so Meson runs ``zfr i18n -b`` into the build dir."""
    po_dir = root / "po"
    meson_path = po_dir / "meson.build"
    if not po_dir.is_dir():
        return []
    if meson_path.is_file():
        original = meson_path.read_text(encoding="utf-8")
        if _MARKER_BEGIN in original and "--compile-mo" in original:
            return []
        updated = _patch_existing(original)
    else:
        updated = (
            "# SPDX-License-Identifier: AGPL-3.0-or-later\n"
            "i18n = import('i18n')\n\n"
            + _DERIVE_BLOCK
            + "\ni18n.gettext(\n"
            "    'zfr',\n"
            "    data_dirs: _po_src,\n"
            "    install: true,\n"
            ")\n"
        )

    rel = str(meson_path.relative_to(root))
    if dry_run:
        return [rel]
    meson_path.write_text(updated, encoding="utf-8")
    return [rel]
