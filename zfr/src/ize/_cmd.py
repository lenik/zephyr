# SPDX-License-Identifier: AGPL-3.0-or-later
"""ize command implementation (separated to keep ize/__init__ import-light)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from i18n import _
from lang import LANGS
from lib import _is_zfr_meta_repo, find_project_dir
from lint.util import _role


def _run_one(spec, files, session, *, dry_run: bool):
    """Run one rule; return its EditList (applied immediately when not dry_run)."""
    from lint.editlist import EditList

    result = spec.ize(files, session)
    if result is None:
        result = EditList()
    if not dry_run:
        result.apply(session.root, dry_run=False)
    return result


def prepare_ize_session(
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
    always: list[str] | None = None,
    only: list[str] | None = None,
    workdir: Path | None = None,
) -> tuple[Any, list]:
    """Build session + gated RuleSpec list (after options / flags)."""
    from std.registry import is_selected, is_suppressed, parse_uncheck
    from std.ize_rules import all_ize_specs
    from lint.session import Session

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
            raise SystemExit(2) from e
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
    forced = parse_uncheck(always)
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
        if r.id in forced or r.code in forced:
            gated.append(r)
            continue
        if is_suppressed(rule_id=r.id, code=r.code, suppressed=suppressed):
            continue
        gated.append(r)
    return session, gated


def plan_ize(
    session,
    gated: list,
    *,
    dry_run: bool = True,
) -> list[tuple[Any, Any]]:
    """Run gated rules (dry-run by default); return ``[(spec, EditList), ...]``.

    When *dry_run* is False, each EditList is applied immediately (chained).
    """
    from lint.editlist import EditList
    from lint.scanner import scan_project, select_scheduled

    root = session.root
    session.dry_run = dry_run
    results: list[tuple[Any, Any]] = []

    mz = [r for r in gated if r.code == "ize.mesonize"]
    rest = [r for r in gated if r.code != "ize.mesonize"]
    if mz:
        _ftor, rule_to_files = scan_project(root, mz, session)
        # always-forced rules with empty files still run
        scheduled_mz = select_scheduled(mz, rule_to_files, require_files=True)
        for spec, files in scheduled_mz:
            ed = _run_one(spec, files, session, dry_run=dry_run)
            results.append((spec, ed))

    _ftor, rule_to_files = scan_project(root, rest, session)
    scheduled = select_scheduled(rest, rule_to_files, require_files=True)
    # Include forced rules that had no file match
    from std.registry import parse_uncheck

    have = {s.id for s, _ in scheduled}
    for r in rest:
        if r.id in have:
            continue
        # forced via session? not tracked — skip empty unless GLOBS=['/']
        if r.globs == ["/"] or (len(r.globs) == 1 and r.globs[0] in ("/", "/**/*")):
            scheduled.append((r, [root]))
    # re-sort
    from lint.scanner import sort_rules

    specs_only = [s for s, _ in scheduled]
    files_map = {s.id: f for s, f in scheduled}
    scheduled = [(s, files_map.get(s.id, [root])) for s in sort_rules(specs_only)]

    for spec, files in scheduled:
        ed = _run_one(spec, files, session, dry_run=dry_run)
        results.append((spec, ed))

    meson_edits = session.flush_meson()
    if meson_edits.edits:
        if not dry_run:
            meson_edits.apply(root, dry_run=False)
        # attach to a synthetic last bucket — callers merge by path
        results.append((None, meson_edits))
    return results


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
    always: list[str] | None = None,
    only: list[str] | None = None,
    workdir: Path | None = None,
    browse: bool = False,
) -> int:
    """Scan → schedule ZI rules → merge EditLists → flush meson ASTs → apply."""
    from std.ize_rules import ize_rule_id
    from lint.editlist import EditList
    from csr import Csr

    if browse:
        from ize.browse import browse_ize

        return browse_ize(
            lang=lang,
            man=man,
            subst=subst,
            mesonize=mesonize,
            uncheck=uncheck,
            always=always,
            only=only,
            workdir=workdir,
            color=color,
        )

    session, gated = prepare_ize_session(
        lang=lang,
        dry_run=dry_run,
        man=man,
        subst=subst,
        mesonize=mesonize,
        commit=commit,
        author=author,
        verbose=verbose,
        color=color,
        uncheck=uncheck,
        always=always,
        only=only,
        workdir=workdir,
    )
    results = plan_ize(session, gated, dry_run=dry_run)
    merged = EditList()
    for _spec, ed in results:
        if ed is not None:
            merged.merge(ed)

    eng = session.options.get("_ize_engine")
    if eng is not None:
        eng.dry_run = dry_run
        eng.report()
    elif not merged.edits:
        print(_("No changes."))
    else:
        csr = Csr(color)
        for ed in merged.edits:
            kind = ed.kind if ed.kind in ("add", "update", "delete", "convert") else "update"
            rid = ize_rule_id(ed.rule) if ed.rule else ""
            tag = f"[{rid}] " if rid and rid != "ZI????" else ""
            print(
                f"{csr.wrap(kind, 'green' if kind == 'add' else 'yellow')}: "
                f"{tag}{ed.path} — {ed.detail}"
            )
    return 0
