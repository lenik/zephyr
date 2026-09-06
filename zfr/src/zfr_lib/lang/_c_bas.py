# SPDX-License-Identifier: AGPL-3.0-or-later
"""C-family (c/cpp/clib/cpplib) bas i18n / logger / gettext spacing helpers.

Lint and ize share these checkers and light source rewrites:

1. Each ``main`` should ``#include <bas/locale/i18n.h>`` + ``<bas/proc/env.h>``,
   call ``self_exe()`` and ``init_i18n(LOCALEDIR)`` (LOCALEDIR from meson config.h).
2. At least one translation unit must ``#include <bas/log/deflog.h>`` and
   ``define_logger();`` (libs may mark it ``__attribute__((weak))``).
3. gettext ``_()`` / ``N_()`` string contents must not start or end with spaces
   (pad outside the gettext call, e.g. separate ``fputs`` for option columns).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ..i18n import _
from .. import is_probably_text, iter_files

C_FAMILY_LANGS = frozenset({"c", "clib", "cpp", "cpplib"})
_SRC_SUFFIXES = {".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}

_INCLUDE_I18N = re.compile(r'#\s*include\s*<bas/locale/i18n\.h>')
_INCLUDE_ENV = re.compile(r'#\s*include\s*<bas/proc/env\.h>')
_INCLUDE_DEFLOG = re.compile(r'#\s*include\s*<bas/log/deflog\.h>')
_SELF_EXE = re.compile(r'\bself_exe\s*\(')
_INIT_I18N = re.compile(r'\binit_i18n\s*\(\s*LOCALEDIR\s*\)')
_DEFINE_LOGGER = re.compile(r'\bdefine_logger\s*\(\s*\)\s*;')
_MAIN_FN = re.compile(r'\bint\s+main\s*\(')
_GETTEXT_CALL = re.compile(
    r'\b(?:N_|_)\(\s*((?:"(?:\\.|[^"\\])*"(?:\s*)+)+)\)',
    re.MULTILINE,
)
_STR_LIT = re.compile(r'"((?:\\.|[^"\\])*)"')


def _src_files(root: Path) -> list[Path]:
    src = root / "src"
    if not src.is_dir():
        return []
    out: list[Path] = []
    for path in iter_files(src):
        if path.suffix.lower() in _SRC_SUFFIXES and is_probably_text(path):
            out.append(path)
    return sorted(out)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _decode_c_string_chunk(raw: str) -> str:
    """Decode one C string-literal body (no surrounding quotes)."""
    out: list[str] = []
    i = 0
    while i < len(raw):
        if raw[i] == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            escapes = {
                "n": "\n",
                "t": "\t",
                "r": "\r",
                "\\": "\\",
                '"': '"',
                "'": "'",
                "0": "\0",
            }
            out.append(escapes.get(nxt, nxt))
            i += 2
            continue
        out.append(raw[i])
        i += 1
    return "".join(out)


def gettext_literal_text(arg_blob: str) -> str:
    """Join adjacent C string literals inside a ``_()`` / ``N_()`` argument."""
    parts = [_decode_c_string_chunk(m.group(1)) for m in _STR_LIT.finditer(arg_blob)]
    return "".join(parts)


def gettext_has_edge_spaces(arg_blob: str) -> bool:
    """True when joined gettext text starts/ends with space or tab (not newline)."""
    text = gettext_literal_text(arg_blob)
    if not text:
        return False
    return text[0] in " \t" or text[-1] in " \t"


def strip_gettext_edge_spaces(arg_blob: str) -> str:
    """Rewrite adjacent string literals so joined text has no leading/trailing space/tab.

    Newlines at the end (common in help strings) are preserved. Only space and tab
    are trimmed from the ends.
    """
    lits = list(_STR_LIT.finditer(arg_blob))
    if not lits:
        return arg_blob
    decoded = [_decode_c_string_chunk(m.group(1)) for m in lits]
    joined = "".join(decoded)
    if not joined or (joined[0] not in " \t" and joined[-1] not in " \t"):
        return arg_blob

    lead = 0
    while lead < len(joined) and joined[lead] in " \t":
        lead += 1
    trail = 0
    while trail < len(joined) - lead and joined[-(trail + 1)] in " \t":
        trail += 1

    remain_lead = lead
    for i, s in enumerate(decoded):
        if remain_lead <= 0:
            break
        if remain_lead >= len(s):
            remain_lead -= len(s)
            decoded[i] = ""
        else:
            decoded[i] = s[remain_lead:]
            remain_lead = 0
    remain_trail = trail
    for i in range(len(decoded) - 1, -1, -1):
        if remain_trail <= 0:
            break
        s = decoded[i]
        if remain_trail >= len(s):
            remain_trail -= len(s)
            decoded[i] = ""
        else:
            decoded[i] = s[: len(s) - remain_trail]
            remain_trail = 0

    def _encode(s: str) -> str:
        return (
            s.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
        )

    new_blob = arg_blob
    for m, s in zip(reversed(lits), reversed(decoded)):
        new_blob = new_blob[: m.start()] + f'"{_encode(s)}"' + new_blob[m.end() :]
    return new_blob


def find_main_sources(root: Path) -> list[Path]:
    return [p for p in _src_files(root) if _MAIN_FN.search(_read(p))]


def has_define_logger(root: Path) -> Path | None:
    for path in _src_files(root):
        text = _read(path)
        if _DEFINE_LOGGER.search(text) and _INCLUDE_DEFLOG.search(text):
            return path
        if _DEFINE_LOGGER.search(text):
            return path
    return None


def lint_c_bas(root: Path, *, lang: str) -> list[Finding]:
    """Lint bas i18n / logger / gettext spacing for a C-family project."""
    if lang not in C_FAMILY_LANGS:
        return []
    out: list[Finding] = []
    mains = find_main_sources(root)

    if not mains:
        out.append(
            Finding(
                "note",
                "lang.c.bas.main",
                _("no int main() in src/; skip bas i18n main checks"),
            )
        )
    else:
        for path in mains:
            rel = _rel(root, path)
            text = _read(path)
            missing: list[str] = []
            if not _INCLUDE_I18N.search(text):
                missing.append("#include <bas/locale/i18n.h>")
            if not _INCLUDE_ENV.search(text):
                missing.append("#include <bas/proc/env.h>")
            if not _SELF_EXE.search(text):
                missing.append("self_exe()")
            if not _INIT_I18N.search(text):
                missing.append("init_i18n(LOCALEDIR)")
            if missing:
                out.append(
                    Finding(
                        "warn",
                        "lang.c.bas.main",
                        _("main missing bas i18n setup: %s") % ", ".join(missing),
                        rel,
                        fix=_(
                            "In main: #include <bas/locale/i18n.h> and <bas/proc/env.h>; "
                            "const char *exe = self_exe(); init_i18n(LOCALEDIR); "
                            "(LOCALEDIR from meson config.h). Run `zfr ize`."
                        ),
                    )
                )
            else:
                out.append(
                    Finding(
                        "ok",
                        "lang.c.bas.main",
                        _("bas i18n main setup (self_exe + init_i18n)"),
                        rel,
                    )
                )

    logger_path = has_define_logger(root)
    if logger_path is None:
        out.append(
            Finding(
                "warn",
                "lang.c.bas.logger",
                _("no define_logger() in src/"),
                "src/",
                fix=_(
                    "In one .c/.cpp: #include <bas/log/deflog.h> then define_logger(); "
                    "libraries may use __attribute__((weak)) define_logger(); "
                    "Run `zfr ize`."
                ),
            )
        )
    else:
        text = _read(logger_path)
        weak = bool(
            re.search(
                r"__attribute__\s*\(\s*\(\s*weak\s*\)\s*\)\s*\n?\s*define_logger\s*\(",
                text,
            )
        )
        detail = _("define_logger() present")
        if weak:
            detail = _("weak define_logger() present (library)")
        if not _INCLUDE_DEFLOG.search(text):
            out.append(
                Finding(
                    "warn",
                    "lang.c.bas.logger",
                    _("define_logger() without #include <bas/log/deflog.h>"),
                    _rel(root, logger_path),
                    fix=_("Add #include <bas/log/deflog.h> before define_logger();"),
                )
            )
        else:
            out.append(
                Finding("ok", "lang.c.bas.logger", detail, _rel(root, logger_path))
            )

    meson = root / "meson.build"
    if meson.is_file():
        mtxt = _read(meson)
        if "LOCALEDIR" not in mtxt:
            out.append(
                Finding(
                    "warn",
                    "lang.c.bas.localedir",
                    _("meson.build missing LOCALEDIR in config.h"),
                    "meson.build",
                    fix=_(
                        "localedir = prefix / get_option('localedir'); "
                        "config_h.set_quoted('LOCALEDIR', localedir); Run `zfr ize`."
                    ),
                )
            )
        else:
            out.append(
                Finding(
                    "ok",
                    "lang.c.bas.localedir",
                    _("meson LOCALEDIR present"),
                    "meson.build",
                )
            )

    space_hits = 0
    for path in _src_files(root):
        text = _read(path)
        for m in _GETTEXT_CALL.finditer(text):
            if gettext_has_edge_spaces(m.group(1)):
                space_hits += 1
                line = text.count("\n", 0, m.start()) + 1
                preview = gettext_literal_text(m.group(1))[:40].replace("\n", "\\n")
                out.append(
                    Finding(
                        "warn",
                        "lang.c.bas.gettext_space",
                        _("gettext string has leading/trailing spaces: %r") % preview,
                        _rel(root, path),
                        line=line,
                        fix=_(
                            "Keep padding outside _(): e.g. fputs(\"  -v, --verbose      \", out); "
                            "fputs(_(\"repeat for more verbose loggings\\n\"), out);"
                        ),
                    )
                )
    if space_hits == 0 and any(_GETTEXT_CALL.search(_read(p)) for p in _src_files(root)):
        out.append(
            Finding(
                "ok",
                "lang.c.bas.gettext_space",
                _("gettext _() strings have no leading/trailing spaces"),
            )
        )

    return out


def _insert_includes(text: str, includes: list[str]) -> str:
    """Insert missing #include lines after the last existing #include block."""
    missing = [inc for inc in includes if inc not in text]
    if not missing:
        return text
    block = "".join(f"{inc}\n" for inc in missing)
    matches = list(re.finditer(r"(?m)^#\s*include\b.*$", text))
    if matches:
        pos = matches[-1].end()
        return text[:pos] + "\n" + block + text[pos:]
    # After copyright / feature-test macros, before first code.
    m = re.search(r"(?m)^(int\s+main\s*\(|define_logger\s*\()", text)
    if m:
        return text[: m.start()] + block + "\n" + text[m.start() :]
    return block + "\n" + text


def ensure_main_bas_i18n(text: str) -> tuple[str, list[str]]:
    """Ensure includes + self_exe/init_i18n in a main translation unit."""
    if not _MAIN_FN.search(text):
        return text, []
    notes: list[str] = []
    new = _insert_includes(
        text,
        [
            "#include <bas/locale/i18n.h>",
            "#include <bas/proc/env.h>",
        ],
    )
    if new != text:
        notes.append("bas i18n/env includes")
        text = new

    if not _SELF_EXE.search(text) or not _INIT_I18N.search(text):
        m = re.search(r"(int\s+main\s*\([^)]*\)\s*\{)", text)
        if m:
            insert = ""
            if not _SELF_EXE.search(text):
                insert += "\n    const char *exe = self_exe();"
            if not _INIT_I18N.search(text):
                insert += "\n    init_i18n(LOCALEDIR);"
            if insert:
                text = text[: m.end()] + insert + text[m.end() :]
                notes.append("self_exe + init_i18n(LOCALEDIR)")
    return text, notes


def ensure_define_logger(text: str, *, weak: bool = False) -> tuple[str, list[str]]:
    """Ensure deflog include + define_logger(); optionally weak (libraries)."""
    notes: list[str] = []
    if _DEFINE_LOGGER.search(text):
        new = _insert_includes(text, ["#include <bas/log/deflog.h>"])
        if new != text:
            notes.append("bas/log/deflog.h include")
        return new, notes

    new = _insert_includes(text, ["#include <bas/log/deflog.h>"])
    if new != text:
        notes.append("bas/log/deflog.h include")
        text = new

    decl = "define_logger();\n"
    if weak:
        decl = "__attribute__((weak))\ndefine_logger();\n"
    # Place after includes, before first function.
    m = re.search(r"(?m)^(int\s+\w+|void\s+\w+|static\s+)", text)
    if m:
        text = text[: m.start()] + "\n" + decl + "\n" + text[m.start() :]
    else:
        text = text.rstrip() + "\n\n" + decl
    notes.append("weak define_logger()" if weak else "define_logger()")
    return text, notes


def fix_gettext_edge_spaces(text: str) -> tuple[str, int]:
    """Strip leading/trailing spaces inside _()/N_() string literals. Returns (text, n)."""
    count = 0
    out: list[str] = []
    pos = 0
    for m in _GETTEXT_CALL.finditer(text):
        out.append(text[pos : m.start()])
        blob = m.group(1)
        prefix = text[m.start() : m.start(1)]
        suffix = text[m.end(1) : m.end()]
        if gettext_has_edge_spaces(blob):
            count += 1
            blob = strip_gettext_edge_spaces(blob)
        out.append(prefix + blob + suffix)
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), count


def ensure_meson_localedir(text: str) -> tuple[str, list[str]]:
    """Ensure localedir path var and config_h LOCALEDIR."""
    notes: list[str] = []
    if re.search(r"set_quoted\s*\(\s*'LOCALEDIR'", text):
        return text, notes

    if not re.search(r"\blocaledir\s*=", text):
        # Prefer after other prefix / get_option lines.
        m = re.search(
            r"(?m)^(prefix\s*=\s*get_option\('prefix'\).*)$",
            text,
        )
        line = "localedir = prefix / get_option('localedir')"
        if m:
            # after block of dir assignments
            pass
        m = re.search(r"(?m)^(mandir\s*=\s*prefix\s*/\s*get_option\('mandir'\).*)$", text)
        if m:
            text = text[: m.end()] + "\n" + line + text[m.end() :]
            notes.append("localedir path")
        else:
            m = re.search(r"(?m)^(datadir\s*=\s*prefix\s*/\s*get_option\('datadir'\).*)$", text)
            if m:
                text = text[: m.end()] + "\n" + line + text[m.end() :]
                notes.append("localedir path")
            elif re.search(r"\bprefix\s*=", text):
                m = re.search(r"(?m)^prefix\s*=.*$", text)
                assert m
                text = text[: m.end()] + "\n" + line + text[m.end() :]
                notes.append("localedir path")

    if not re.search(r"set_quoted\s*\(\s*'LOCALEDIR'", text):
        m = re.search(
            r"(?m)^(config_h\.set(?:_quoted)?\([^)]*\)\s*)$",
            text,
        )
        # Insert after last config_h.set*
        sets = list(re.finditer(r"(?m)^config_h\.set(?:_quoted)?\(.*\)$", text))
        if sets:
            pos = sets[-1].end()
            text = (
                text[:pos]
                + "\nconfig_h.set_quoted('LOCALEDIR', localedir)"
                + text[pos:]
            )
            notes.append("config_h LOCALEDIR")
        elif "configuration_data()" in text:
            text = text.replace(
                "configuration_data()",
                "configuration_data()\nconfig_h.set_quoted('LOCALEDIR', localedir)",
                1,
            )
            notes.append("config_h LOCALEDIR")
    return text, notes


def ensure_meson_bas_dep(text: str, *, lang: str) -> tuple[str, list[str]]:
    """Ensure dependency('bas-c'|'bas-cpp') is declared and linked into executables."""
    notes: list[str] = []
    pkg = "bas-cpp" if lang in {"cpp", "cpplib"} else "bas-c"
    var = "bas_cpp_dep" if pkg == "bas-cpp" else "bas_c_dep"
    args_kw = "cpp_args" if lang in {"cpp", "cpplib"} else "c_args"

    if not re.search(rf"dependency\s*\(\s*'{re.escape(pkg)}'", text) and not re.search(
        rf"\b{re.escape(var)}\s*=", text
    ):
        snippet = f"\n{var} = dependency('{pkg}', required: true)\n"
        m = re.search(
            r"(?ms)configure_file\s*\([^)]*configuration:\s*config_h,?[^)]*\)",
            text,
        )
        if m:
            text = text[: m.end()] + snippet + text[m.end() :]
        else:
            text = text.rstrip() + snippet
        notes.append(f"dependency('{pkg}')")

    # TEXT_DOMAIN / LOGGER_NAME macros used by bas init_i18n / define_logger.
    if "TEXT_DOMAIN" not in text:
        args_snip = (
            f"\nbas_args = ["
            f"'-DLOGGER_NAME=' + meson.project_name(), "
            f"'-DTEXT_DOMAIN=' + meson.project_name()"
            f"]\n"
            f"{args_kw}_bas = bas_args\n"
        )
        m = re.search(rf"\b{re.escape(var)}\s*=\s*dependency\([^)]+\)", text)
        if m:
            text = text[: m.end()] + args_snip + text[m.end() :]
            notes.append(f"{args_kw} TEXT_DOMAIN/LOGGER_NAME")

    # Wire into executable(...) that lack this dependency.
    if re.search(r"\bexecutable\s*\(", text) and not re.search(
        rf"dependencies:\s*\[[^\]]*\b{re.escape(var)}\b", text
    ):
        def _wire_exe(m: re.Match[str]) -> str:
            block = m.group(0)
            if var in block:
                return block
            # Insert dependencies before install: or closing ).
            if re.search(r"\bdependencies\s*:", block):
                return re.sub(
                    r"(dependencies\s*:\s*\[)",
                    rf"\1{var}, ",
                    block,
                    count=1,
                )
            if re.search(r"\n(\s*)install\s*:", block):
                return re.sub(
                    r"\n(\s*)install\s*:",
                    rf"\n\1dependencies: [{var}],\n\1install:",
                    block,
                    count=1,
                )
            return block

        text2, n = re.subn(
            r"executable\s*\((?:[^()]|\([^()]*\))*\)",
            _wire_exe,
            text,
            flags=re.S,
        )
        if n and text2 != text:
            text = text2
            notes.append(f"executable dependencies: [{var}]")

    # Attach bas compile args when we introduced them and executable has no c_args/cpp_args.
    if f"{args_kw}_bas" in text and re.search(r"\bexecutable\s*\(", text):
        def _wire_args(m: re.Match[str]) -> str:
            block = m.group(0)
            if args_kw in block:
                return block
            if re.search(r"\n(\s*)install\s*:", block):
                return re.sub(
                    r"\n(\s*)install\s*:",
                    rf"\n\1{args_kw}: {args_kw}_bas,\n\1install:",
                    block,
                    count=1,
                )
            return block

        text2, n = re.subn(
            r"executable\s*\((?:[^()]|\([^()]*\))*\)",
            _wire_args,
            text,
            flags=re.S,
        )
        if n and text2 != text:
            text = text2
            notes.append(f"executable {args_kw}: {args_kw}_bas")

    return text, notes


def bas_build_depends(lang: str) -> list[str]:
    if lang in {"cpp", "cpplib"}:
        return ["libbas-cpp-dev"]
    return ["libbas-c-dev"]


def prefer_weak_logger(lang: str, root: Path) -> bool:
    if lang in {"clib", "cpplib"}:
        return True
    return False


def logger_target_file(root: Path, lang: str) -> Path | None:
    """Where to inject define_logger when missing."""
    if lang == "clib":
        p = root / "src" / "lib.c"
        if p.is_file():
            return p
    if lang == "cpplib":
        p = root / "src" / "lib.cpp"
        if p.is_file():
            return p
    mains = find_main_sources(root)
    if mains:
        return mains[0]
    files = _src_files(root)
    return files[0] if files else None
