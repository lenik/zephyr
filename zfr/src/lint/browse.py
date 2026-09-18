# SPDX-License-Identifier: AGPL-3.0-or-later
"""``zfr lint -b/--browse`` — local web UI for lint results."""

from __future__ import annotations

import html
import json
import os
import sys
import tempfile
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from fdm import FdmCapture, CHAN_ERR, fdmux_capture, iter_runs, which_fdm_tool
from finding import Finding
from i18n import _
from pkgfields import _meson_project_fields
from std import LINT_RULES
from versioning import cli_version
from .browse_page import _shell_html
from .comments import (
    append_comment,
    comments_for_rule,
    project_comments_path,
    user_comments_path,
)
from .docs import rule_doc_dict
from .fdm_html import fdm_to_html
from .ize_map import ize_command_for_lint, ize_targets_for_lint

_UI_MAPS_CACHE: dict[str, dict[str, str]] | None = None
_LOCALES_CACHE: list[str] | None = None


# Browse chrome strings (msgid = English). Literals use _("…") for xgettext.
def _browse_ui_msgids() -> dict[str, str]:
    """English msgids for browse UI (also forces gettext extraction)."""
    return {
        "title": _("zfr lint"),
        "show_all": _("Show all rules (including passed)"),
        "locale": _("Language"),
        "refresh": _("Re-lint"),
        "status": _("status"),
        "errors": _("errors"),
        "warnings": _("warnings"),
        "notes": _("notes"),
        "ok": _("ok"),
        "solve": _("Solve"),
        "show": _("Show"),
        "output": _("Output"),
        "fix": _("fix"),
        "no_findings": _(
            "No findings to display (toggle “show all” for passed checks)."
        ),
        "running": _("Running…"),
        "fdmux_missing": _("fdmux is required (install the fdmux package)."),
        "docs": _("Documentation"),
        "add_comment": _("Add Comment"),
        "enter_comments": _("Enter comments…"),
        "project_only": _("This project only"),
        "submit": _("Submit"),
        "rule_state": _("Rule"),
        "saved": _("Saved"),
        "close": _("Close"),
        "pass_rate": _("pass"),
        "theme_light": _("Light"),
        "theme_dark": _("Dark"),
        "sort": _("Sort"),
        "sort_id": _("ID"),
        "sort_status": _("Status"),
        "sort_name": _("Name"),
        "request_new": _("Request for new"),
        "request_hint": _(
            "Suggest a new lint rule (what to check, why, how)…"
        ),
    }


def _ui(lang: str) -> dict[str, str]:
    """Return browse chrome strings for *lang* (via gettext)."""
    _set_locale(lang)
    return _browse_ui_msgids()


def _ui_maps() -> dict[str, dict[str, str]]:
    global _UI_MAPS_CACHE
    if _UI_MAPS_CACHE is not None:
        return _UI_MAPS_CACHE
    maps: dict[str, dict[str, str]] = {}
    for lang in _available_locales():
        maps[lang] = _ui(lang)
    _UI_MAPS_CACHE = maps
    return maps


def _available_locales() -> list[str]:
    global _LOCALES_CACHE
    if _LOCALES_CACHE is not None:
        return _LOCALES_CACHE
    locales = ["en"]
    from i18n.messages import _source_root

    for cand in (Path.cwd() / "po" / "LINGUAS", _source_root() / "po" / "LINGUAS"):
        if cand.is_file():
            for line in cand.read_text(encoding="utf-8").splitlines():
                line = line.split("#", 1)[0].strip()
                if line and line not in locales:
                    locales.append(line)
            break
    _LOCALES_CACHE = locales
    return locales


def _env_ui_lang() -> str:
    """Pick browse UI locale from LANGUAGE / LC_* / LANG (matched to LINGUAS)."""
    from i18n.messages import _wanted_languages

    available = _available_locales()
    avail_set = set(available)
    wanted = _wanted_languages() or []
    for tag in wanted:
        if tag in avail_set:
            return tag
        base = tag.split("_", 1)[0]
        if base in avail_set:
            return base
        for loc in available:
            if loc == base or loc.startswith(base + "_"):
                return loc
    return "en"


def _set_locale(lang: str) -> None:
    import i18n.messages as messages

    if lang in ("en", "C", "POSIX"):
        os.environ["LANGUAGE"] = "en"
        os.environ["LC_MESSAGES"] = "C"
        os.environ["LANG"] = "C"
    else:
        os.environ["LANGUAGE"] = lang
        os.environ["LC_ALL"] = ""
        os.environ["LC_MESSAGES"] = lang
        os.environ["LANG"] = lang
    messages._translation = None  # type: ignore[attr-defined]
    messages.init_i18n()


def _author_info(root: Path) -> str:
    meson = _meson_project_fields(root)
    author = meson.get("project_author") or ""
    email = meson.get("project_email") or ""
    if author and email:
        return f"{author} <{email}>"
    if author:
        return author
    try:
        from .util import _control

        src, _, _ = _control(root)
        return src.get("Maintainer") or ""
    except Exception:
        return ""


def _rule_states(root: Path) -> dict[str, str]:
    from lintsel import RuleState, load_rule_rows

    return {r.rule.id: r.state.value for r in load_rule_rows(root)}


def _finding_payload(
    f: Finding, root: Path, rule_states: dict[str, str], *, ui_lang: str
) -> dict[str, Any]:
    targets = ize_targets_for_lint(f.code)
    rule = LINT_RULES.lookup(f.code)
    rid = f.rule_id
    docs = rule_doc_dict(rid, f.code, lang=ui_lang)
    comments = comments_for_rule(root, rid)
    return {
        "severity": f.severity,
        "rule_id": rid,
        "code": f.code,
        "message": f.message,
        "file": f.file,
        "line": f.line,
        "fix": f.fix,
        "izeable": bool(rule and rule.izeable and targets),
        "ize_targets": targets,
        "ize_cmd": ize_command_for_lint(f.code),
        "docs": docs,
        "comments": comments,
        "rule_state": rule_states.get(rid, "default"),
    }


def _counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"error": 0, "warn": 0, "note": 0, "ok": 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    return counts


def _collect_payload(
    root: Path,
    *,
    l10n_level: str,
    uncheck: list[str] | None,
    always: list[str] | None,
    warning_level: str | None,
    error_level: str | None,
    ui_lang: str,
) -> dict[str, Any]:
    from . import collect_findings
    from .filtering import filter_findings
    from .severity import remap_severities
    from l10n import apply_lint_option_file
    import argparse
    from . import add_arguments as lint_add_arguments

    # Merge live lint.options (rule toggles) into uncheck/always
    parser = argparse.ArgumentParser(add_help=False)
    lint_add_arguments(parser)
    ns = parser.parse_args([])
    ns.uncheck = list(uncheck or [])
    ns.always = list(always or [])
    ns = apply_lint_option_file(root, parser, ns)

    name, lang, role, findings = collect_findings(root, l10n_level=l10n_level)
    findings = filter_findings(findings, ns.uncheck, getattr(ns, "always", None))
    remap_severities(findings, as_warning=warning_level, as_error=error_level)
    states = _rule_states(root)
    items = [_finding_payload(f, root, states, ui_lang=ui_lang) for f in findings]
    counts = _counts(items)
    total = max(1, sum(counts.values()))
    maps = _ui_maps()
    return {
        "root": str(root),
        "name": name,
        "lang": lang,
        "role": role,
        "ui_lang": ui_lang,
        "ui": maps.get(ui_lang) or _ui(ui_lang),
        "ui_maps": maps,
        "locales": _available_locales(),
        "findings": items,
        "counts": counts,
        "rates": {
            "ok": counts["ok"] / total,
            "warn": counts["warn"] / total,
            "error": counts["error"] / total,
            "note": counts["note"] / total,
        },
        "zfr_version": cli_version(),
        "author": _author_info(root),
        "comments_paths": {
            "project": str(project_comments_path(root)),
            "user": str(user_comments_path()),
        },
        "new_requests": _new_requests_text(root),
    }


def _new_requests_text(root: Path) -> str:
    nr = comments_for_rule(root, "NEW")
    parts = [p.rstrip() for p in (nr.get("project"), nr.get("user")) if p and p.strip()]
    return ("\n\n".join(parts) + "\n") if parts else ""


def _remap_payload_lang(payload: dict[str, Any], ui_lang: str) -> dict[str, Any]:
    """Swap UI chrome + per-rule markdown docs without re-running lint."""
    _set_locale(ui_lang)
    out = dict(payload)
    out["ui_lang"] = ui_lang
    out["ui"] = (_ui_maps().get(ui_lang) or _ui(ui_lang))
    out["ui_maps"] = _ui_maps()
    out["locales"] = _available_locales()
    findings: list[dict[str, Any]] = []
    for item in payload.get("findings") or []:
        row = dict(item)
        row["docs"] = rule_doc_dict(row["rule_id"], row["code"], lang=ui_lang)
        findings.append(row)
    out["findings"] = findings
    return out


class _BrowseState:
    def __init__(
        self,
        root: Path,
        *,
        l10n_level: str,
        uncheck: list[str] | None,
        always: list[str] | None,
        warning_level: str | None,
        error_level: str | None,
        zfr_exe: list[str],
        default_lang: str,
    ) -> None:
        self.root = root
        self.l10n_level = l10n_level
        self.uncheck = uncheck
        self.always = always
        self.warning_level = warning_level
        self.error_level = error_level
        self.zfr_exe = zfr_exe
        self.default_lang = default_lang
        self.lock = threading.Lock()
        self.ize_outputs: dict[str, dict[str, Any]] = {}
        self.payload: dict[str, Any] | None = None
        self.ready = threading.Event()
        self._error: BaseException | None = None

    def collect(self, ui_lang: str) -> dict[str, Any]:
        _set_locale(ui_lang)
        payload = _collect_payload(
            self.root,
            l10n_level=self.l10n_level,
            uncheck=self.uncheck,
            always=self.always,
            warning_level=self.warning_level,
            error_level=self.error_level,
            ui_lang=ui_lang,
        )
        self.payload = payload
        return payload

    def get_payload(self, ui_lang: str, *, refresh: bool) -> dict[str, Any]:
        self.ready.wait(timeout=120)
        if self._error is not None:
            raise self._error
        with self.lock:
            if refresh or self.payload is None:
                return self.collect(ui_lang)
            cached = self.payload
            if cached.get("ui_lang") == ui_lang:
                return cached
            remapped = _remap_payload_lang(cached, ui_lang)
            self.payload = remapped
            return remapped

    def prewarm(self) -> None:
        def _run() -> None:
            try:
                with self.lock:
                    self.collect(self.default_lang)
            except BaseException as exc:  # noqa: BLE001 — surface to /api/data
                self._error = exc
            finally:
                self.ready.set()

        threading.Thread(target=_run, name="lint-browse-prewarm", daemon=True).start()


def _fdm_has_err(data: bytes) -> bool:
    return any(ch == CHAN_ERR for ch, _ in iter_runs(data))


def _make_handler(state: _BrowseState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("[lint-browse] " + (fmt % args) + "\n")

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj: Any, code: int = 200) -> None:
            self._send(
                code,
                json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                body = _shell_html(state.default_lang).encode("utf-8")
                self._send(200, body, "text/html; charset=utf-8")
                return
            if parsed.path == "/api/data":
                qs = urllib.parse.parse_qs(parsed.query)
                ui_lang = (qs.get("lang") or [state.default_lang])[0] or state.default_lang
                refresh = (qs.get("refresh") or ["0"])[0] in ("1", "true", "yes")
                try:
                    payload = state.get_payload(ui_lang, refresh=refresh)
                except BaseException as exc:  # noqa: BLE001
                    self._json({"ok": False, "error": str(exc)}, 500)
                    return
                self._json(payload)
                return
            self._send(404, b"not found\n", "text/plain; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                req = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self._json({"ok": False, "error": "bad json"}, 400)
                return

            if parsed.path == "/api/ize":
                self._api_ize(req)
                return
            if parsed.path == "/api/comment":
                self._api_comment(req)
                return
            if parsed.path == "/api/rule-state":
                self._api_rule_state(req)
                return
            self._json({"ok": False, "error": "not found"}, 404)

        def _api_ize(self, req: dict[str, Any]) -> None:
            code = str(req.get("code") or "")
            targets = ize_targets_for_lint(code)
            cmd_str = ize_command_for_lint(code) or ""
            if not targets:
                self._json({"ok": False, "exit_code": 2, "cmd": cmd_str, "html": "<p>not izeable</p>"})
                return
            if which_fdm_tool("fdmux") is None:
                u = _ui(str(req.get("lang") or state.default_lang))
                self._json(
                    {
                        "ok": False,
                        "exit_code": 127,
                        "cmd": cmd_str,
                        "html": f"<p class='sev-error'>{html.escape(u['fdmux_missing'])}</p>",
                    }
                )
                return
            argv = list(state.zfr_exe) + ["ize", "-v"]
            for t in targets:
                argv.extend(["--only", t])
            fd, tmp = tempfile.mkstemp(prefix="zfr-lint-ize-", suffix=".fdm")
            os.close(fd)
            tmp_path = Path(tmp)
            try:
                cap = FdmCapture(tmp_path)
                rc = fdmux_capture(argv, cap, cwd=state.root)
                data = tmp_path.read_bytes()
                out_html = fdm_to_html(data)
                has_err = rc != 0 or _fdm_has_err(data)
            finally:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            result = {
                "ok": rc == 0 and not has_err,
                "exit_code": rc,
                "cmd": cmd_str,
                "html": out_html,
                "has_err": has_err,
            }
            with state.lock:
                state.ize_outputs[code] = result
            self._json(result)

        def _api_comment(self, req: dict[str, Any]) -> None:
            rid = str(req.get("rule_id") or "")
            text = str(req.get("text") or "")
            project_only = bool(req.get("project_only", False))
            if not rid or not text.strip():
                self._json({"ok": False, "error": "empty"})
                return
            path = (
                project_comments_path(state.root)
                if project_only
                else user_comments_path()
            )
            with state.lock:
                append_comment(path, rid, text)
            self._json({"ok": True, "path": str(path)})

        def _api_rule_state(self, req: dict[str, Any]) -> None:
            from lintsel import RuleState, RuleRow, load_rule_rows, save_rule_rows

            rid = str(req.get("rule_id") or "").upper()
            st = str(req.get("state") or "default")
            try:
                state_e = RuleState(st)
            except ValueError:
                self._json({"ok": False, "error": "bad state"})
                return
            with state.lock:
                rows = load_rule_rows(state.root)
                found = False
                for row in rows:
                    if row.rule.id == rid:
                        row.state = state_e
                        found = True
                        break
                if not found:
                    rule = LINT_RULES.by_id(rid)
                    if rule is None:
                        self._json({"ok": False, "error": "unknown rule"})
                        return
                    rows.append(RuleRow(rule=rule, state=state_e))
                save_rule_rows(state.root, rows)
            self._json({"ok": True, "rule_id": rid, "state": st})

    return Handler


def _resolve_zfr_exe() -> list[str]:
    zfr_src = Path(__file__).resolve().parents[1] / "zfr"
    # src/lint/browse.py → src/zfr
    if zfr_src.is_file():
        return [sys.executable, str(zfr_src)]
    return [sys.executable, str(Path(sys.argv[0]).resolve())]


def browse_lint(
    root: Path,
    *,
    l10n_level: str = "L1",
    uncheck: list[str] | None = None,
    always: list[str] | None = None,
    warning_level: str | None = None,
    error_level: str | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = True,
) -> int:
    """Serve lint browse SPA and block until interrupted."""
    default_lang = _env_ui_lang()
    state = _BrowseState(
        root,
        l10n_level=l10n_level,
        uncheck=uncheck,
        always=always,
        warning_level=warning_level,
        error_level=error_level,
        zfr_exe=_resolve_zfr_exe(),
        default_lang=default_lang,
    )
    # Overlap lint with browser startup / HTML fetch.
    state.prewarm()
    httpd = ThreadingHTTPServer((host, port), _make_handler(state))
    bound = httpd.server_address[1]
    url = f"http://{host}:{bound}/"
    print(_("zfr lint browse: %s") % url, flush=True)
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
