# SPDX-License-Identifier: AGPL-3.0-or-later
"""Language-specific lint bits."""

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

def check_lang_bits(root: Path, lang: str) -> list[Finding]:
    out: list[Finding] = []
    if lang == "bash":
        ins = list((root / "src").glob("*.in")) if (root / "src").is_dir() else []
        if ins:
            out.append(Finding("ok", "lang.bash.src", f"src scripts: {', '.join(p.name for p in ins)}"))
        else:
            out.append(
                Finding(
                    "warn",
                    "lang.bash.src",
                    "no src/*.in scripts",
                    "src/",
                    fix="Keep configured scripts as src/<puff>.in with @PACKAGE@/@VERSION@ "
                    "and meson configure_file + install_mode rwxr-xr-x.",
                )
            )
    elif lang in ("c", "clib", "cpp", "cpplib"):
        if not (root / "tests").is_dir():
            out.append(
                Finding(
                    "note",
                    "lang.tests",
                    "no tests/ directory",
                    "tests/",
                    fix="Add tests/ and meson test() entries like the C family templates.",
                )
            )
        else:
            out.append(Finding("ok", "lang.tests", "tests/ present"))
    elif lang == "python":
        if (root / "tests").is_dir():
            out.append(Finding("ok", "lang.python.tests", "tests/ present"))
        else:
            out.append(
                Finding(
                    "warn",
                    "lang.python.tests",
                    "no tests/ (python template uses unittest + meson test)",
                    "tests/",
                    fix="Add tests/test_*.py and meson test() with PYTHONPATH=src.",
                )
            )
    elif lang == "rust" and not (root / "Cargo.toml").is_file():
        out.append(
            Finding(
                "error",
                "lang.rust.cargo",
                "missing Cargo.toml",
                "Cargo.toml",
                fix="Rust zephyr projects keep Cargo.toml plus meson custom_target for the binary.",
            )
        )
    elif lang == "go" and not (root / "go.mod").is_file():
        out.append(
            Finding(
                "error",
                "lang.go.mod",
                "missing go.mod",
                "go.mod",
                fix="Add go.mod; meson should `go build` with -X main.buildVersion from meson.project_version().",
            )
        )
    return out
