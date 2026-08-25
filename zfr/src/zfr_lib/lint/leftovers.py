# SPDX-License-Identifier: AGPL-3.0-or-later
"""README and leftover-token checks."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from .. import (
    LANGS,
    RECOMMENDED_I18N_LINGUAS,
    RECOMMENDED_I18N_SOURCE,
    TEMPLATE_PUFF,
    _is_zfr_cli_package,
    _is_zfr_meta_repo,
    changelog_version,
    detect_lang,
    find_project_dir,
    is_probably_text,
    iter_files,
    template_dir,
    version_file_version,
)
from ..csr import Csr
from ..packaging import _meson_project_fields, _parse_control_stanzas
from .finding import Finding
from .util import *  # noqa: F403

def check_readme(root: Path, role: str) -> list[Finding]:
    out: list[Finding] = []
    for name in ("README.md", "README-zh.md"):
        path = root / name
        if not path.is_file() and _is_zfr_cli_package(root):
            path = root.parent / name
        if not path.is_file():
            continue
        text = _read(path)
        marker = _PLACEHOLDER_README if name == "README.md" else _PLACEHOLDER_README_ZH
        has_banner = marker in text or _PLACEHOLDER_README in text
        if has_banner:
            if role == "template":
                out.append(
                    Finding(
                        "note",
                        f"readme.placeholder.{name}",
                        _("%s keeps the template placeholder banner (apps must rewrite it)") % name,
                        name,
                        line=1,
                        fix=_("After `zfr create`/`zfr rename`, rewrite this README and remove "
                        "the generated-from-template banner. Templates should keep this banner."),
                    )
                )
            else:
                out.append(
                    Finding(
                        "error",
                        f"readme.placeholder.{name}",
                        _("%s still has the template placeholder banner") % name,
                        name,
                        line=1,
                        fix=_("Rewrite %s for this project. Remove the generated-from-template "
                        "banner and describe the real commands, build, and license.") % name,
                    )
                )
        else:
            out.append(Finding("ok", f"readme.{name}", _("%s has no template banner") % name, name))
    return out


# Instantiated apps call the zfr CLI for version/dist. The tool name "zfr"
# is never a leftover template token. Legacy lines that still say
# "zephyr version" contain the placeholder word and are exempted here.
_ZEPHYR_CLI_LINE = re.compile(
    r"zephyr\s+version"
    r"|zephyr\s+dist"
    r"|zephyr\s+is expected"
    r"|zephyr\s+on PATH"
    r"|zephyr not found"
    r"|command\s+-v\s+zephyr"
    r"|tools/zephyr"
    r"|`zephyr\s+",
    re.I,
)


def _leftover_line(line: str, token: re.Pattern[str]) -> bool:
    if not token.search(line):
        return False
    return not _ZEPHYR_CLI_LINE.search(line)


def check_leftovers(root: Path, role: str) -> list[Finding]:
    if role != "app":
        return [
            Finding(
                "ok",
                "tokens.template",
                _("%s tree may contain zephyr/some_puff1 placeholders (expected)") % role,
            )
        ]
    hits = 0
    samples: list[str] = []
    token = re.compile(rf"\b({re.escape(TEMPLATE_PUFF)}|zephyr)\b", re.I)
    for path in iter_files(root):
        rel = path.relative_to(root)
        parts = {rel.as_posix(), path.name}
        rel_posix = rel.as_posix()
        skip_cli = rel_posix.startswith(("tools/zfr", "zfr/", "src/zfr"))
        if any(token.search(p) for p in parts) and not skip_cli:
            hits += 1
            if len(samples) < 8:
                samples.append(str(rel))
        if not path.is_file() or not is_probably_text(path):
            continue
        text = _read(path)
        for i, line in enumerate(text.splitlines(), 1):
            if _leftover_line(line, token):
                hits += 1
                if len(samples) < 8:
                    samples.append(f"{rel}:{i}")
                break
    if hits:
        preview = ", ".join(samples)
        more = "" if hits <= 8 else _(" (+%d more)") % (hits - len(samples))
        return [
            Finding(
                "error",
                "tokens.leftover",
                _("found %(hits)d leftover template token(s) (zephyr/%(token)s): %(preview)s%(more)s")
                % {"hits": hits, "token": TEMPLATE_PUFF, "preview": preview, "more": more},
                fix=_("Run `zfr rename <project> [puff ...]` or replace remaining zephyr/some_puff1 "
                "identifiers. After create, leftover tokens mean instantiation failed."),
            )
        ]
    return [Finding("ok", "tokens.leftover", _("no leftover zephyr/some_puff1 tokens"))]
