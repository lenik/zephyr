# SPDX-License-Identifier: AGPL-3.0-or-later
"""ize command implementation (separated to keep ize/__init__ import-light)."""

from __future__ import annotations

import sys
from pathlib import Path

from i18n import _
from lang import LANGS
from lib import _is_zfr_meta_repo, find_project_dir
from lint.util import _role


def cmd_ize(
    *,
    lang: str | None = None,
    dry_run: bool = False,
    man: bool = True,
    subst: bool = True,
    mesonize: bool = True,
    commit: bool = False,
    author: str | None = None,
    verbose: bool = False,
    color: str = "auto",
    uncheck: list[str] | None = None,
    only: list[str] | None = None,
    workdir: Path | None = None,
) -> int:
    """Scan → schedule ZI rules → merge EditLists → flush meson ASTs → apply."""
    from std.registry import is_selected, is_suppressed, parse_uncheck
    from std.ize_rules import all_ize_specs, ize_rule_id
    from lint.editlist import EditList
    from lint.scanner import scan_project, select_scheduled
    from lint.session import Session
    from csr import Csr
    from ize.util import Change

    if commit and dry_run:
        raise SystemExit("zfr ize: --commit cannot be combined with --dry-run")
    root = find_project_dir(workdir)
    if _is_zfr_meta_repo(root):
        raise SystemExit(
            f"{root} looks like the zephyr meta-repo. "
            "Run zfr ize from a language project, not the repository root."
        )
    role = _role(root)
    if lang:
        if lang not in LANGS:
            raise SystemExit(f"unknown language {lang!r} (one of: {', '.join(LANGS)})")
        detected = lang
    else:
        from lib import detect_lang

        try:
            detected = detect_lang(root)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            print(
                "pass -l LANG to ize a project whose language could not be detected",
                file=sys.stderr,
            )
            return 2
    if role == "meta":
        raise SystemExit("zfr ize does not operate on the meta-repo root")

    session = Session(
        root=root,
        lang=detected,
        role=role,
        dry_run=dry_run,
        verbose=verbose,
        do_man=man,
        do_subst=subst,
        do_mesonize=mesonize,
        do_commit=commit,
        author=author,
        options={"color": color},
    )
    suppressed = parse_uncheck(uncheck)
    only_set = parse_uncheck(only)
    rules = all_ize_specs()
    gated = []
    for r in rules:
        if r.code.startswith("ize.man.") and not man:
            continue
        if r.code == "ize.subst" and not subst:
            continue
        if r.code == "ize.mesonize" and not mesonize:
            continue
        if r.code == "ize.commit" and not commit:
            continue
        if not is_selected(rule_id=r.id, code=r.code, only=only_set):
            continue
        if is_suppressed(rule_id=r.id, code=r.code, suppressed=suppressed):
            continue
        gated.append(r)

    _ftor, rule_to_files = scan_project(root, gated, session)
    scheduled = select_scheduled(gated, rule_to_files, require_files=True)

    merged = EditList()
    changes: list[Change] = []
    for spec, files in scheduled:
        result = spec.ize(files, session)
        if result is None:
            continue
        merged.merge(result)
        for ed in result.edits:
            kind = ed.kind if ed.kind in ("add", "update", "delete", "convert") else "update"
            changes.append(Change(kind, ed.path, ed.detail, rule=ed.rule or spec.code))

    merged.merge(session.flush_meson())
    merged.apply(root, dry_run=dry_run)

    csr = Csr(color)
    if not changes and not merged.edits:
        print(_("No changes."))
    else:
        for ch in changes:
            rid = ize_rule_id(ch.rule) if ch.rule else ""
            tag = f"[{rid}] " if rid and rid != "ZI????" else ""
            print(
                f"{csr.wrap(ch.kind, 'green' if ch.kind == 'add' else 'yellow')}: "
                f"{tag}{ch.path} — {ch.detail}"
            )
    return 0
