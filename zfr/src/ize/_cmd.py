# SPDX-License-Identifier: AGPL-3.0-or-later
"""ize command implementation (separated to keep ize/__init__ import-light)."""

from __future__ import annotations

import sys
from pathlib import Path

from i18n import _
from lang import LANGS
from lib import _is_zfr_meta_repo, find_project_dir
from lint.util import _role


def _run_rules(scheduled, session, merged, *, dry_run: bool) -> None:
    """Run scheduled rules; apply each EditList immediately so later rules see writes."""
    for spec, files in scheduled:
        result = spec.ize(files, session)
        if result is None:
            continue
        merged.merge(result)
        # Flush per-rule so the next step reads updated meson/control/etc. from disk
        # (engine helpers still use Path.read_text, not an overlay).
        result.apply(session.root, dry_run=dry_run)


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

    merged = EditList()

    # Pass 1: ize.mesonize may create meson.build; apply before the main scan so
    # meson.* / subst rules can match the new file.
    mz = [r for r in gated if r.code == "ize.mesonize"]
    rest = [r for r in gated if r.code != "ize.mesonize"]
    if mz:
        _ftor, rule_to_files = scan_project(root, mz, session)
        scheduled_mz = select_scheduled(mz, rule_to_files, require_files=True)
        _run_rules(scheduled_mz, session, merged, dry_run=dry_run)

    _ftor, rule_to_files = scan_project(root, rest, session)
    scheduled = select_scheduled(rest, rule_to_files, require_files=True)
    _run_rules(scheduled, session, merged, dry_run=dry_run)

    meson_edits = session.flush_meson()
    merged.merge(meson_edits)
    meson_edits.apply(root, dry_run=dry_run)

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
