# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bridge: run one legacy Ize step and capture writes into an EditList."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from lint.editlist import EditList
from lint.session import Session


def _ensure_engine(session: Session):
    eng = session.options.get("_ize_engine")
    if eng is not None:
        return eng
    from ize.engine import Ize

    eng = Ize(
        session.root,
        lang=session.lang,
        # Honour session dry-run so 2meson / side-effect steps match CLI -n.
        # File writes still go through the patched write_text → EditList path.
        dry_run=session.dry_run,
        do_man=session.do_man,
        do_subst=session.do_subst,
        do_mesonize=session.do_mesonize,
        do_commit=session.do_commit,
        author=session.author,
        verbose=session.verbose,
        color=session.options.get("color", "auto"),
        uncheck=[],
        only=[],
    )
    edits: EditList = session.options.setdefault("_ize_edits", EditList())
    _orig_write = eng.write_text
    _orig_copy = eng.copy_file

    def write_text(path: Path, text: str, detail: str, *, kind: str = "add") -> None:
        rel = str(path.relative_to(session.root)).replace("\\", "/") if path.is_absolute() else str(path)
        try:
            rel = str(Path(path).resolve().relative_to(session.root.resolve())).replace("\\", "/")
        except Exception:
            from lint.util import _rel

            rel = _rel(session.root, Path(path))
        existed = Path(path).is_file() if Path(path).is_absolute() else (session.root / rel).is_file()
        edits.write(
            rel,
            text,
            detail=detail,
            rule=eng._current_rule,
            kind="update" if existed else "add",
        )
        eng.note("update" if existed else "add", rel, detail)

    def copy_file(src: Path, dest: Path, detail: str) -> None:
        try:
            rel = str(dest.resolve().relative_to(session.root.resolve())).replace("\\", "/")
        except Exception:
            from lint.util import _rel

            rel = _rel(session.root, dest)
        edits.copy(src, rel, detail=detail, rule=eng._current_rule, executable=True)
        eng.note("add", rel, detail)

    eng.write_text = write_text  # type: ignore[method-assign]
    eng.copy_file = copy_file  # type: ignore[method-assign]
    eng._editlist = edits  # type: ignore[attr-defined]
    session.options["_ize_engine"] = eng
    return eng


def run_step(session: Session, rule_code: str, fn: Callable[[Any], None]) -> EditList:
    """Run *fn(engine)* capturing edits; returns only edits produced by this call."""
    eng = _ensure_engine(session)
    edits: EditList = session.options["_ize_edits"]
    before = len(edits.edits)
    prev = eng._current_rule
    eng._current_rule = rule_code
    try:
        fn(eng)
    finally:
        eng._current_rule = prev
    chunk = EditList()
    chunk.edits = list(edits.edits[before:])
    return chunk
