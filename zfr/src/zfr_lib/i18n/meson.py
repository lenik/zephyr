# SPDX-License-Identifier: AGPL-3.0-or-later
"""Meson po/meson.build hooks for build-time derived locale generation."""

from __future__ import annotations

import re
from pathlib import Path

_MARKER_BEGIN = "# zfr: i18n-derive-begin"
_MARKER_END = "# zfr: i18n-derive-end"

# Features required for a complete derive+install hook (upgrade if missing).
_REQUIRED_SNIPPETS = (
    "--compile-mo",
    "project_source_root",
    "add_install_script",
    "MESON_INSTALL_DESTDIR_PREFIX",
    # Absolute stamp path: after `cd` to source, relative @OUTPUT@ lands in po/.
    "_po_build / 'i18n-derive.stamp'",
    # Install flat build/po/*.po (no .derive.sig sidecar).
    'for f in "$po"/*.po',
)

# Portable shell install (no dependency on a newer zfr --install-derived flag).
# split('\\n') in this raw string writes split('\n') into meson.build.
_DERIVE_BLOCK = r"""# zfr: i18n-derive-begin
_po_src = meson.current_source_dir()
_po_build = meson.current_build_dir()
_sh = find_program('sh')
_po_dep_list = run_command(
  _sh, '-c', 'cd "$1" && ls -1 *.po LINGUAS 2>/dev/null || true',
  _po_src, check: false,
).stdout().strip().split('\n')
_po_dep_files = []
foreach _p : _po_dep_list
  if _p != ''
    _po_dep_files += [_p]
  endif
endforeach

_zfr_i18n = find_program('zfr', native: true, required: false)
if _zfr_i18n.found()
  # Run from project source so zfr can discover package metadata / docs/.
  # Stamp must be absolute: command cds to source, so relative @OUTPUT@ would
  # be written under source po/ and ninja would rebuild every time.
  custom_target(
    'i18n-derive',
    command: [
      _sh, '-c',
      'cd "$1" && shift && exec "$@"',
      '_',
      meson.project_source_root(),
      _zfr_i18n, 'i18n', '-b',
      '--po-dir', _po_build,
      '--stamp', _po_build / 'i18n-derive.stamp',
      '--compile-mo',
      '--domain', meson.project_name(),
    ],
    output: 'i18n-derive.stamp',
    depend_files: _po_dep_files,
    build_by_default: true,
    console: true,
  )
  # i18n.gettext only installs LINGUAS; copy .mo for each flat derived *.po.
  meson.add_install_script(
    _sh, '-c',
    # sh -c SCRIPT $0 $1 $2 — first arg after SCRIPT is $0.
    'po="$0"; domain="$1"; loc="$2"; base="${MESON_INSTALL_DESTDIR_PREFIX:-${DESTDIR:-}${MESON_INSTALL_PREFIX:-}}"; for f in "$po"/*.po; do [ -e "$f" ] || continue; lang=${f##*/}; lang=${lang%.po}; mo="$po/$lang/LC_MESSAGES/$domain.mo"; [ -f "$mo" ] || continue; dest="$base/$loc/$lang/LC_MESSAGES/$domain.mo"; mkdir -p "$(dirname "$dest")"; install -m644 "$mo" "$dest"; done',
    _po_build,
    meson.project_name(),
    get_option('localedir'),
  )
endif
# zfr: i18n-derive-end
"""

_BLOCK_RE = re.compile(
    re.escape(_MARKER_BEGIN) + r".*?" + re.escape(_MARKER_END) + r"\n?",
    re.DOTALL,
)


def _hook_complete(text: str) -> bool:
    if _MARKER_BEGIN not in text:
        return False
    return all(s in text for s in _REQUIRED_SNIPPETS)


def _insert_derive_block(text: str) -> str:
    if _MARKER_BEGIN in text:
        text = _BLOCK_RE.sub(_DERIVE_BLOCK + "\n", text, count=1)
    elif "i18n = import('i18n')" in text:
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
    """Patch ``po/meson.build`` so Meson builds and installs derived locales."""
    po_dir = root / "po"
    meson_path = po_dir / "meson.build"
    if not po_dir.is_dir():
        return []
    if meson_path.is_file():
        original = meson_path.read_text(encoding="utf-8")
        if _hook_complete(original):
            return []
        updated = _insert_derive_block(original)
    else:
        domain = "zephyr"
        updated = (
            "# SPDX-License-Identifier: AGPL-3.0-or-later\n"
            "i18n = import('i18n')\n\n"
            + _DERIVE_BLOCK
            + "\ni18n.gettext(\n"
            f"    '{domain}',\n"
            "    data_dirs: _po_src,\n"
            "    install: true,\n"
            ")\n"
        )
        root_meson = root / "meson.build"
        if root_meson.is_file():
            match = re.search(
                r"project\s*\(\s*['\"]([^'\"]+)['\"]",
                root_meson.read_text(encoding="utf-8"),
            )
            if match:
                updated = updated.replace(f"'{domain}'", f"'{match.group(1)}'", 1)

    rel = str(meson_path.relative_to(root))
    if dry_run:
        return [rel]
    meson_path.write_text(updated, encoding="utf-8")
    return [rel]
