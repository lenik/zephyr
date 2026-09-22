# SPDX-License-Identifier: AGPL-3.0-or-later
"""``zfr ize -b/--browse`` — browser UI for matching ize rules + EditList diffs."""

from __future__ import annotations

import difflib
import html
import json
import sys
import threading
import webbrowser
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from typing import Any

from i18n import _
from lint.comments import (
    append_comment,
    comments_for_rule,
    project_comments_path,
    user_comments_path,
)
from lint.docs import rule_doc_dict
from lint.editlist import EditList, TextEdit

_ASSETS = Path(__file__).resolve().parent / "browse_assets"


def _editlist_to_diffs(root: Path, edits: EditList) -> list[dict[str, Any]]:
    """Build unified-diff payloads for each write/delete/copy in *edits*."""
    out: list[dict[str, Any]] = []
    for ed in edits.edits:
        rel = ed.path
        dest = root / rel
        old = ""
        if ed.kind in ("write", "update", "add", "convert") and dest.is_file():
            try:
                old = dest.read_text(encoding="utf-8", errors="replace")
            except OSError:
                old = ""
        new = ed.content or ""
        if ed.kind == "delete":
            new = ""
            if dest.is_file():
                try:
                    old = dest.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    old = ""
        if ed.kind == "copy":
            src = Path(ed.source) if ed.source else None
            if src is not None and not src.is_absolute():
                src = root / ed.source
            if src is not None and src.is_file():
                try:
                    new = src.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    new = f"(binary or unreadable: {ed.source})"
            old = ""
        if old == new and ed.kind not in ("delete", "copy", "chmod"):
            continue
        udiff = "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
                n=3,
            )
        )
        out.append(
            {
                "path": rel,
                "kind": ed.kind,
                "detail": ed.detail,
                "rule": ed.rule,
                "diff": udiff or f"--- a/{rel}\n+++ b/{rel}\n(no textual diff)\n",
                "diff_html": _diff_to_html(udiff, rel),
            }
        )
    return out


def _diff_to_html(udiff: str, path: str) -> str:
    """Render unified diff with +/- line classes; optional pygments on path."""
    if not udiff:
        return f"<pre class='diff empty'>{html.escape(path)}: (no change)</pre>"
    lines_out: list[str] = ["<pre class='diff'>"]
    for line in udiff.splitlines():
        esc = html.escape(line)
        if line.startswith("+++") or line.startswith("---"):
            cls = "diff-file"
        elif line.startswith("@@"):
            cls = "diff-hunk"
        elif line.startswith("+"):
            cls = "diff-add"
        elif line.startswith("-"):
            cls = "diff-del"
        else:
            cls = "diff-ctx"
        lines_out.append(f"<span class='{cls}'>{esc}</span>\n")
    lines_out.append("</pre>")
    return "".join(lines_out)


def _rule_states(root: Path) -> dict[str, str]:
    from izesel import load_rule_rows

    return {row.rule.id: row.state.value for row in load_rule_rows(root)}


class _IzeBrowseState:
    def __init__(
        self,
        *,
        lang: str | None,
        man: bool,
        subst: bool,
        mesonize: bool,
        uncheck: list[str] | None,
        always: list[str] | None,
        only: list[str] | None,
        workdir: Path | None,
        color: str,
    ) -> None:
        self.kwargs = dict(
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
        self.lock = threading.Lock()
        self.ready = threading.Event()
        self._error: BaseException | None = None
        self.payload: dict[str, Any] | None = None
        self._edits: dict[str, EditList] = {}
        self.root: Path | None = None

    def collect(self) -> dict[str, Any]:
        from ize._cmd import prepare_ize_session, plan_ize

        session, gated = prepare_ize_session(dry_run=True, **self.kwargs)
        self.root = session.root
        results = plan_ize(session, gated, dry_run=True)
        states = _rule_states(session.root)
        self._edits = {}
        rules_out: list[dict[str, Any]] = []
        for spec, ed in results:
            if spec is None:
                continue
            self._edits[spec.id] = ed
            diffs = _editlist_to_diffs(session.root, ed)
            # edit_count / nop reflect effective pending changes (content-equal
            # writes are dropped in diffs), not raw EditList length.
            rules_out.append(
                {
                    "rule_id": spec.id,
                    "code": spec.code,
                    "title": spec.title,
                    "state": states.get(spec.id, "default"),
                    "edit_count": len(diffs),
                    "nop": len(diffs) == 0,
                    "paths": sorted({d["path"] for d in diffs}),
                    "docs": rule_doc_dict(spec.id, spec.code, lang="en"),
                    "comments": comments_for_rule(session.root, spec.id),
                    "diffs": diffs,
                }
            )
        self.payload = {
            "root": str(session.root),
            "lang": session.lang,
            "rules": rules_out,
            "comments_paths": {
                "project": str(project_comments_path(session.root)),
                "user": str(user_comments_path()),
            },
        }
        return self.payload

    def get_payload(self, *, refresh: bool = False) -> dict[str, Any]:
        self.ready.wait(timeout=180)
        if self._error is not None:
            raise self._error
        with self.lock:
            if refresh or self.payload is None:
                return self.collect()
            return self.payload

    def apply_rule(self, rule_id: str) -> dict[str, Any]:
        with self.lock:
            ed = self._edits.get(rule_id)
            if ed is None or self.root is None:
                return {"ok": False, "error": "unknown rule or no edits"}
            ed.apply(self.root, dry_run=False)
            # drop applied
            self._edits[rule_id] = EditList()
            return {"ok": True, "rule_id": rule_id, "applied": len(ed.edits)}

    def apply_all(self) -> dict[str, Any]:
        with self.lock:
            if self.root is None:
                return {"ok": False, "error": "not ready"}
            n = 0
            for rid, ed in list(self._edits.items()):
                ed.apply(self.root, dry_run=False)
                n += len(ed.edits)
                self._edits[rid] = EditList()
            return {"ok": True, "applied": n}

    def prewarm(self) -> None:
        def _run() -> None:
            try:
                self.collect()
            except BaseException as e:
                self._error = e
            finally:
                self.ready.set()

        threading.Thread(target=_run, daemon=True).start()


@lru_cache(maxsize=4)
def _shell_html() -> str:
    html_t = (_ASSETS / "shell.html").read_text(encoding="utf-8")
    css = (_ASSETS / "browse.css").read_text(encoding="utf-8")
    js = (_ASSETS / "browse.js").read_text(encoding="utf-8")
    return Template(html_t).safe_substitute(title="zfr ize", css=css, js=js)


def _make_handler(state: _IzeBrowseState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def _json(self, obj: Any, code: int = 200) -> None:
            data = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _read_json(self) -> dict[str, Any]:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            try:
                return json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return {}

        def do_GET(self) -> None:  # noqa: N802
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                body = _shell_html().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/api/data":
                qs = parse_qs(parsed.query)
                refresh = qs.get("refresh", ["0"])[0] in ("1", "true", "yes")
                try:
                    self._json(state.get_payload(refresh=refresh))
                except BaseException as e:
                    self._json({"ok": False, "error": str(e)}, 500)
                return
            self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            from urllib.parse import urlparse

            parsed = urlparse(self.path)
            body = self._read_json()
            if parsed.path == "/api/apply":
                self._json(state.apply_rule(str(body.get("id") or "")))
                return
            if parsed.path == "/api/apply-all":
                self._json(state.apply_all())
                return
            if parsed.path == "/api/comment":
                from lint.comments import normalize_rule_key

                rid = normalize_rule_key(str(body.get("rule_id") or ""), default_prefix="ZI")
                text = str(body.get("text") or "")
                project_only = bool(body.get("project_only"))
                if state.root is None:
                    self._json({"ok": False, "error": "not ready"})
                    return
                append_comment(state.root, rid, text, project_only=project_only)
                self._json({"ok": True})
                return
            if parsed.path == "/api/rule-state":
                from izesel import RuleState, RuleRow, load_rule_rows, save_rule_rows
                from std import IZE_RULES

                if state.root is None:
                    self._json({"ok": False, "error": "not ready"})
                    return
                rid = str(body.get("rule_id") or "")
                st = str(body.get("state") or "default")
                try:
                    state_e = RuleState(st)
                except ValueError:
                    self._json({"ok": False, "error": "bad state"})
                    return
                rows = load_rule_rows(state.root)
                found = False
                for row in rows:
                    if row.rule.id == rid:
                        row.state = state_e
                        found = True
                        break
                if not found:
                    rule = IZE_RULES.by_id(rid)
                    if rule is None:
                        self._json({"ok": False, "error": "unknown rule"})
                        return
                    rows.append(RuleRow(rule=rule, state=state_e))
                save_rule_rows(state.root, rows)
                self._json({"ok": True, "rule_id": rid, "state": st})
                return
            self.send_error(404)

    return Handler


def browse_ize(
    *,
    lang: str | None = None,
    man: bool = True,
    subst: bool = True,
    mesonize: bool = True,
    uncheck: list[str] | None = None,
    always: list[str] | None = None,
    only: list[str] | None = None,
    workdir: Path | None = None,
    color: str = "auto",
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = True,
) -> int:
    state = _IzeBrowseState(
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
    state.prewarm()
    httpd = ThreadingHTTPServer((host, port), _make_handler(state))
    bound = httpd.server_address[1]
    url = f"http://{host}:{bound}/"
    print(_("zfr ize browse: %s") % url, flush=True)
    print(_("Press Ctrl+C to stop."), flush=True)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(file=sys.stderr)
        return 0
    finally:
        httpd.server_close()
    return 0
