# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize helpers — externalize meson run_target scripts under scripts/."""

from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from ...i18n import _
from ..util import _rel

if TYPE_CHECKING:
    from . import Ize

_SCRIPT_TARGETS = (
    "posync",
    "look",
    "install-symlinks",
    "uninstall-symlinks",
    "deploy",
)

_RUN_TARGET_RE = re.compile(
    r"(run_target\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*command\s*:\s*\[)(.*?)(\]\s*,?\s*\))",
    re.S,
)

_INLINE_BODY_RE = re.compile(
    r"""(?sx)
    ['\"]bash['\"]\s*,\s*
    ['\"]-[^'\"]*['\"]\s*,\s*
    (?:'''(.*?)'''|\"\"\"(.*?)\"\"\"|'(.*?)'|\"(.*?)\")
    """
)


def _extract_inline_body(command: str) -> str | None:
    m = _INLINE_BODY_RE.search(command)
    if not m:
        return None
    body = next((g for g in m.groups() if g is not None), None)
    if body is None:
        return None
    return textwrap.dedent(body).strip("\n") + "\n"


def _uses_scripts(command: str, name: str) -> bool:
    needle = f"scripts/{name}"
    if needle in command.replace("\\", "/"):
        return True
    return bool(
        re.search(
            rf"['\"]scripts['\"]\s*/\s*['\"]{re.escape(name)}\.(?:sh|bash)['\"]",
            command,
        )
    )


def _scripts_command_snippet(name: str) -> str:
    return (
        f"\n        'bash',\n"
        f"        meson.project_source_root() / 'scripts' / '{name}.sh',\n"
        f"        meson.project_source_root(),\n"
        f"        meson.project_build_root(),\n    "
    )


def _default_posync_script(project_name: str) -> str:
    pot = f"{project_name}.pot"
    return f"""#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Sync gettext catalogs from current sources (meson run_target posync).
set -euo pipefail
SOURCE_ROOT="${{1:-${{MESON_SOURCE_ROOT:-.}} }}"
cd "$SOURCE_ROOT/po"
xgettext --from-code=UTF-8 --keyword=_ --language=Python --directory=.. \\
    --output={pot} --files-from=POTFILES
while IFS= read -r lang; do
    [ -n "$lang" ] || continue
    case "$lang" in
        '#'* ) continue ;;
    esac
    po_file="$lang.po"
    if [ ! -f "$po_file" ]; then
        msginit --no-translator --input={pot} --locale="$lang" --output-file="$po_file"
    fi
    msgmerge --update --backup=none "$po_file" {pot}
    msgattrib --no-obsolete --output-file="$po_file" "$po_file"
done < LINGUAS
"""


def _wrap_script(body: str, *, source_root_arg: bool = True) -> str:
    """Turn an extracted meson inline body into a standalone scripts/*.sh."""
    # Replace meson placeholders commonly used in templates.
    body = body.replace("@SOURCE_ROOT@", "${SOURCE_ROOT}")
    body = body.replace("@BUILD_ROOT@", "${BUILD_ROOT}")
    body = body.replace('"', '"')  # no-op keep
    # Meson often uses "@0@" style — leave as-is if present.
    header = [
        "#!/usr/bin/env bash",
        "# SPDX-License-Identifier: AGPL-3.0-or-later",
        "# Generated/maintained for meson run_target; invoked as:",
        "#   bash scripts/<name>.sh <SOURCE_ROOT> <BUILD_ROOT>",
        "set -euo pipefail",
        'SOURCE_ROOT="${1:-${MESON_SOURCE_ROOT:-.}}"',
        'BUILD_ROOT="${2:-${MESON_BUILD_ROOT:-.}}"',
        "",
    ]
    # If body already cds / assumes cwd, keep it after env setup.
    return "\n".join(header) + body.lstrip("\n")


def ensure_scripts_externalized(
    ize: "Ize",
    *,
    targets: tuple[str, ...] | None = None,
) -> None:
    """Extract inline run_target scripts to scripts/ and rewire meson.build."""
    wanted = set(targets) if targets is not None else set(_SCRIPT_TARGETS)
    meson = ize.root / "meson.build"
    if not meson.is_file():
        # Still move root *.sh when no meson.
        _move_root_shells(ize, wanted)
        return
    text = meson.read_text(encoding="utf-8")
    scripts_dir = ize.root / "scripts"
    changed = False
    new_text = text
    offset_adjust = 0

    for m in list(_RUN_TARGET_RE.finditer(text)):
        name = m.group(2)
        if name not in wanted:
            continue
        command = m.group(3)
        if _uses_scripts(command, name):
            continue
        body = _extract_inline_body(command)
        if body is None and name != "posync":
            continue
        scripts_dir.mkdir(parents=True, exist_ok=True)
        script_path = scripts_dir / f"{name}.sh"
        if not script_path.is_file():
            if body is None and name == "posync":
                content = _default_posync_script(ize.name if hasattr(ize, "name") else ize.root.name)
            elif body is not None:
                content = _wrap_script(body)
            else:
                continue
            ize.write_text(
                script_path,
                content,
                f"externalize run_target {name}",
            )
            if not ize.dry_run and script_path.is_file():
                mode = script_path.stat().st_mode
                script_path.chmod(mode | 0o111)
        start = m.start(3) + offset_adjust
        end = m.end(3) + offset_adjust
        snippet = _scripts_command_snippet(name)
        new_text = new_text[:start] + snippet + new_text[end:]
        offset_adjust += len(snippet) - (end - start)
        changed = True
        rule = "ize.posync" if name == "posync" else "ize.scripts"
        ize.note(
            "update",
            "meson.build",
            _("run_target('%s') → scripts/%s.sh") % (name, name),
            rule=rule,
        )

    if changed and new_text != text:
        ize.write_text(meson, new_text, "run_target scripts/ externalization")

    _move_root_shells(ize, wanted)


def _move_root_shells(ize: "Ize", wanted: set[str]) -> None:
    """Move known maintenance shells from project root into scripts/."""
    scripts_dir = ize.root / "scripts"
    known = {f"{t}.sh" for t in _SCRIPT_TARGETS}
    for path in sorted(ize.root.glob("*.sh")):
        if path.name not in known and path.stem not in wanted:
            continue
        # When this pass is posync-only, only move posync.sh.
        if wanted == {"posync"} and path.name != "posync.sh":
            continue
        dest = scripts_dir / path.name
        if dest.exists():
            continue
        scripts_dir.mkdir(parents=True, exist_ok=True)
        rel = _rel(ize.root, path)
        ize.note("move", rel, f"→ scripts/{path.name}", rule="ize.scripts")
        if not ize.dry_run:
            dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            dest.chmod(path.stat().st_mode)
            path.unlink()
