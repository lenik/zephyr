
# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr lint — validate a project against zephyr packaging and layout style."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import _is_zfr_cli_package, detect_lang, find_project_dir
from ..cli import register_command
from ..i18n import _
from ..packaging import _meson_project_fields
from .debian import check_debian
from .finding import Finding
from .i18n_check import check_i18n
from .identity import check_identity
from .lang_bits import check_lang_bits
from .layout import check_layout
from .leftovers import check_leftovers, check_readme
from .meson import check_meson
from .report import format_report
from .rpm import check_rpm
from .template import check_template_gaps
from .util import _control, _role, _specs

# collect_findings / cmd_lint live below if not imported from util
def _resolve_lint_root(root: Path) -> Path:
    """Lint the zfr CLI package when cwd is the zephyr meta-repo root."""
    if _role(root) == "meta":
        cli = root / "zfr"
        if _is_zfr_cli_package(cli):
            return cli
    return root


def collect_findings(root: Path) -> tuple[str, str, str, list[Finding]]:
    root = _resolve_lint_root(root)
    role = _role(root)
    if role == "meta":
        lang = "meta"
    else:
        try:
            lang = detect_lang(root)
        except SystemExit:
            lang = "unknown"
    meson = _meson_project_fields(root)
    src, _, _ = _control(root)
    name = src.get("Source") or meson.get("name") or root.name
    findings: list[Finding] = []
    findings.extend(check_layout(root, lang, role))
    findings.extend(check_identity(root, lang, role))
    findings.extend(check_meson(root, lang))
    findings.extend(check_debian(root, lang, role))
    findings.extend(check_rpm(root, lang))
    findings.extend(check_readme(root, role))
    findings.extend(check_i18n(root, role))
    findings.extend(check_leftovers(root, role))
    findings.extend(check_lang_bits(root, lang))
    findings.extend(check_template_gaps(root, lang, role))
    return name, lang, role, findings

def cmd_lint(
    *,
    verbose: bool = False,
    quiet: bool = False,
    color: str = "auto",
    strict: bool = False,
    workdir: Path | None = None,
) -> int:
    root = _resolve_lint_root(find_project_dir(workdir))
    name, lang, role, findings = collect_findings(root)
    sys.stdout.write(
        format_report(
            root, name, lang, role, findings, verbose=verbose, quiet=quiet, color=color
        )
    )
    sys.stdout.flush()
    errors = sum(1 for f in findings if f.severity == "error")
    warns = sum(1 for f in findings if f.severity == "warn")
    if errors:
        return 1
    if strict and warns:
        return 1
    return 0


NAME = "lint"
HELP = _('validate project packaging and zephyr layout (walks parents from cwd)')
DESCRIPTION = _('Check the current zephyr project for missing files and packaging/style mistakes. Walks from cwd toward parent directories. CSR colors when stdout is a TTY.')


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("-v", "--verbose", action="store_true", help=_("show passing checks too"))
    p.add_argument("-q", "--quiet", action="store_true", help=_("only print errors"))
    p.add_argument("--strict", action="store_true", help=_("treat warnings as failures (exit 1)"))
    p.add_argument("--color", choices=("auto", "always", "never"), default="auto", help=_("CSR (console SGR) highlighting (default: auto)"))


def run(args: argparse.Namespace) -> int:
    return cmd_lint(verbose=args.verbose, quiet=args.quiet, color=args.color, strict=args.strict)


def register(sub: argparse._SubParsersAction) -> None:
    register_command(
        sub,
        NAME,
        help=HELP,
        description=DESCRIPTION,
        add_arguments=add_arguments,
        run=run,
    )
