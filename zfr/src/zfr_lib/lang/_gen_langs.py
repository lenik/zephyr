#!/usr/bin/env python3
"""One-off generator for lang/*.py modules (run from lang/ dir)."""
from __future__ import annotations

from pathlib import Path

HEADER = '''# SPDX-License-Identifier: AGPL-3.0-or-later
"""{title} template language."""
from __future__ import annotations

import re
from pathlib import Path

from ..finding import Finding
from ._puff_helpers import merge_puff, puff_dir_if_exists, puff_generic, puff_paths
from ._spec import LangSpec, WireSpec

NAME = "{name}"

'''


def w(name: str, body: str) -> None:
    Path(f"{name}.py").write_text(body, encoding="utf-8")
    print("wrote", name)


def main() -> None:
    w("bash", HEADER.format(title="Bash", name="bash") + '''
def _score_bash(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    if re.search(r"\\bbash-shlib\\b", depends, re.I):
        scores["bash"] += 14.0
        return
    from .. import iter_files
    src = root / "src"
    bases = [root] + ([src] if src.is_dir() else [])
    for base in bases:
        try:
            paths = [p for p in base.iterdir() if p.is_file()] if base == root else list(iter_files(base))
        except OSError:
            continue
        for path in paths:
            try:
                head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
            except OSError:
                continue
            if re.search(r"\\bimport\\s+cliboot\\b", head) or re.search(
                r"(?:^|\\n)\\s*\\. shlib(?:-import)?\\b|\\bshlib-import\\b", head
            ):
                scores["bash"] += 14.0
                return

def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.in", "{stem}.bash", "docs/{stem}.adoc"))

def _lint(root: Path, role: str) -> list[Finding]:
    ins = list((root / "src").glob("*.in")) if (root / "src").is_dir() else []
    if ins:
        return [Finding("ok", "lang.bash.src", f"src scripts: {', '.join(p.name for p in ins)}")]
    return [Finding("warn", "lang.bash.src", "no src/*.in scripts", "src/",
        fix="Keep configured scripts as src/<puff>.in with @PACKAGE@/@VERSION@ "
        "and meson configure_file + install_mode rwxr-xr-x.")]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".sh": 1.2, ".bash": 3.0},
    shebangs=((re.compile(r"^#!.*\\b(bash|sh)\\b"), 3.0),),
    depends=((re.compile(r"\\bbash-shlib\\b", re.I), 18.0), (re.compile(r"\\bbash\\b", re.I), 8.0)),
    wire=WireSpec(kind="script", app_list="app_scripts", script_ext="in"),
    puff_fn=_puff,
    lint_fn=_lint,
    score_fn=_score_bash,
)
''')

    c_lint = '''
def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.tests", "tests/ present")]
    return [Finding("note", "lang.tests", "no tests/ directory", "tests/",
        fix="Add tests/ and meson test() entries like the C family templates.")]
'''
    c_puff = '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.c", "tests/{stem}_test.c", "{stem}.bash", "docs/{stem}.adoc"))
'''
    w("c", HEADER.format(title="C", name="c") + c_puff + c_lint + '''
SPEC = LangSpec(
    name=NAME,
    ext_weights={".c": 2.0},
    wire=WireSpec(kind="c", app_ext="c", test_ext="c"),
    puff_fn=_puff,
    lint_fn=_lint,
)
''')

    clib_score = '''
def _score_clib(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    ok = bool(re.search(r"\\bshared_library\\s*\\(", meson_txt))
    ok = ok or (re.search(r"\\bpkgconfig\\.generate\\s*\\(", meson_txt) and (root / "src" / "lib.c").is_file())
    ok = ok or ((root / "src" / "lib.c").is_file() and re.search(
        r"\\bbas-c\\b|\\blibbas-c(?:-dev)?\\b", meson_txt + "\\n" + depends, re.I))
    if ok:
        scores["clib"] += 22.0
        scores["c"] *= 0.2
    else:
        if scores["c"]:
            scores["c"] += 4.0
        scores["clib"] *= 0.2
'''
    w("clib", HEADER.format(title="C library (clib)", name="clib") + clib_score + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.c", "src/{stem}.h", "tests/{stem}_test.c", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))
''' + c_lint + '''
SPEC = LangSpec(
    name=NAME,
    ext_weights={".c": 2.0, ".h": 0.45},
    depends=((re.compile(r"\\blibbas-c-dev\\b", re.I), 16.0),),
    meson_tokens={"c": 18.0, "clib": 18.0},
    wire=WireSpec(kind="c", app_ext="c", test_ext="c"),
    puff_fn=_puff,
    lint_fn=_lint,
    score_fn=_score_clib,
    skip_shared_example=True,
)
''')

    cpp_puff = '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.cpp", "tests/{stem}_test.cpp", "{stem}.bash", "docs/{stem}.adoc"))
'''
    w("cpp", HEADER.format(title="C++", name="cpp") + cpp_puff + c_lint + '''
SPEC = LangSpec(
    name=NAME,
    ext_weights={".cpp": 3.0, ".cc": 3.0, ".cxx": 3.0, ".hpp": 2.0, ".hh": 2.0, ".hxx": 2.0, ".h": 0.35},
    wire=WireSpec(kind="c", app_ext="cpp", test_ext="cpp"),
    puff_fn=_puff,
    lint_fn=_lint,
)
''')

    cpplib_score = '''
def _score_cpplib(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    ok = bool(re.search(r"\\bshared_library\\s*\\(", meson_txt))
    ok = ok or (re.search(r"\\bpkgconfig\\.generate\\s*\\(", meson_txt) and (root / "src" / "lib.cpp").is_file())
    ok = ok or ((root / "src" / "lib.cpp").is_file() and re.search(
        r"\\bbas-cpp\\b|\\blibbas-cpp(?:-dev)?\\b", meson_txt + "\\n" + depends, re.I))
    if ok:
        scores["cpplib"] += 22.0
        scores["cpp"] *= 0.2
    else:
        if scores["cpp"]:
            scores["cpp"] += 4.0
        scores["cpplib"] *= 0.2
'''
    w("cpplib", HEADER.format(title="C++ library (cpplib)", name="cpplib") + cpplib_score + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.cpp", "src/{stem}.hpp", "tests/{stem}_test.cpp", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))
''' + c_lint + '''
SPEC = LangSpec(
    name=NAME,
    ext_weights={".cpp": 3.0, ".cc": 3.0, ".cxx": 3.0, ".hpp": 2.0, ".hh": 2.0, ".hxx": 2.0, ".h": 0.35},
    depends=((re.compile(r"\\blibbas-cpp-dev\\b", re.I), 16.0),),
    meson_tokens={"cpp": 18.0, "cpplib": 18.0},
    wire=WireSpec(kind="c", app_ext="cpp", test_ext="cpp"),
    puff_fn=_puff,
    lint_fn=_lint,
    score_fn=_score_cpplib,
    skip_shared_example=True,
)
''')

    w("csharp", HEADER.format(title="C#", name="csharp") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_dir_if_exists(tmpl, f"apps/{stem}"), puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".cs": 4.0},
    depends=((re.compile(r"\\bdotnet(?:-sdk)?\\b", re.I), 12.0),),
    wire=WireSpec(kind="csharp"),
    puff_fn=_puff,
)
''')

    w("erlang", HEADER.format(title="Erlang", name="erlang") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.erl", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".erl": 4.0, ".hrl": 2.0},
    name_weights={"mix.exs": 8.0, "rebar.config": 20.0},
    depends=((re.compile(r"\\berlang\\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
''')

    w("go", HEADER.format(title="Go", name="go") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_dir_if_exists(tmpl, f"cmd/{stem}"), puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "go.mod").is_file():
        return []
    return [Finding("error", "lang.go.mod", "missing go.mod", "go.mod",
        fix="Add go.mod; meson should `go build` with -X main.buildVersion from meson.project_version().")]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".go": 4.0},
    name_weights={"go.mod": 30.0, "go.sum": 8.0},
    depends=((re.compile(r"\\bgolang(?:-go)?\\b", re.I), 12.0),),
    wire=WireSpec(kind="go"),
    puff_fn=_puff,
    lint_fn=_lint,
)
''')

    w("haskell", HEADER.format(title="Haskell", name="haskell") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"), puff_paths(tmpl, stem, "src/Main.hs"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".hs": 4.0, ".lhs": 3.0},
    name_weights={"stack.yaml": 20.0, "cabal.project": 15.0},
    depends=((re.compile(r"\\b(ghc|haskell-devscripts)\\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
''')

    w("java", HEADER.format(title="Java", name="java") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/Main.java", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _score_java(root: Path, scores: dict[str, float], meson_txt: str, depends: str) -> None:
    if re.search(r"\\bjavac\\b|\\bjava\\b", meson_txt) and ".java" in meson_txt:
        scores["java"] += 8.0

def _spec_files(puffs: list[str]) -> list[str]:
    return ["%{_datadir}/%{name}/"]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".java": 4.0},
    name_weights={"pom.xml": 18.0, "build.gradle": 12.0, "build.gradle.kts": 8.0},
    depends=((re.compile(r"\\b(default-jdk|default-jre|openjdk|java-runtime)\\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    spec_files_fn=_spec_files,
    score_fn=_score_java,
)
''')

    w("perl", HEADER.format(title="Perl", name="perl") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.pl", "{stem}.bash", "docs/{stem}.adoc"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".pl": 4.0, ".pm": 3.5, ".t": 2.0},
    name_weights={"makefile.pl": 12.0, "cpanfile": 12.0},
    shebangs=((re.compile(r"^#!.*\\bperl\\b"), 4.0),),
    depends=((re.compile(r"\\bperl\\b", re.I), 8.0),),
    wire=WireSpec(kind="script", app_list="app_scripts", script_ext="pl"),
    puff_fn=_puff,
)
''')

    w("python", HEADER.format(title="Python", name="python") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.py", "tests/test_{stem}.py", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "tests").is_dir():
        return [Finding("ok", "lang.python.tests", "tests/ present")]
    return [Finding("warn", "lang.python.tests", "no tests/ (python template uses unittest + meson test)", "tests/",
        fix="Add tests/test_*.py and meson test() with PYTHONPATH=src.")]

def _spec_files(puffs: list[str]) -> list[str]:
    return ["%{_bindir}/commons.py"]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".py": 3.0, ".pyi": 1.5},
    shebangs=((re.compile(r"^#!.*\\bpython(?:3(?:\\.\\d+)?)?\\b"), 4.0),),
    depends=((re.compile(r"\\bpython3(?:-dev)?\\b", re.I), 10.0),),
    meson_tokens={"python": 18.0},
    meson_hints=(("import('python')", 16.0), ('import("python")', 16.0)),
    wire=WireSpec(kind="python"),
    puff_fn=_puff,
    lint_fn=_lint,
    spec_files_fn=_spec_files,
)
''')

    w("ruby", HEADER.format(title="Ruby", name="ruby") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.rb", "src/commons.rb", "{stem}.bash", "docs/{stem}.adoc"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".rb": 4.0},
    name_weights={"gemfile": 20.0, "rakefile": 8.0},
    shebangs=((re.compile(r"^#!.*\\bruby\\b"), 4.0),),
    depends=((re.compile(r"\\bruby\\b", re.I), 8.0),),
    wire=WireSpec(kind="script", app_list="app_scripts", script_ext="rb"),
    puff_fn=_puff,
)
''')

    w("rust", HEADER.format(title="Rust", name="rust") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/main.rs", "src/lib.rs", "build-aux/cargo-build.sh", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

def _lint(root: Path, role: str) -> list[Finding]:
    if (root / "Cargo.toml").is_file():
        return []
    return [Finding("error", "lang.rust.cargo", "missing Cargo.toml", "Cargo.toml",
        fix="Rust zephyr projects keep Cargo.toml plus meson custom_target for the binary.")]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".rs": 4.0},
    name_weights={"cargo.toml": 30.0, "cargo.lock": 8.0},
    depends=((re.compile(r"\\b(cargo|rustc)\\b", re.I), 12.0),),
    meson_tokens={"rust": 20.0},
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    lint_fn=_lint,
)
''')

    w("smalltalk", HEADER.format(title="GNU Smalltalk", name="smalltalk") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.st", "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".st": 4.0},
    depends=((re.compile(r"\\bgnu-smalltalk\\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
''')

    w("swift", HEADER.format(title="Swift", name="swift") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "{stem}.bash", "docs/{stem}.adoc", "po/{stem}.pot"), puff_paths(tmpl, stem, "src/main.swift"))

SPEC = LangSpec(
    name=NAME,
    ext_weights={".swift": 4.0},
    name_weights={"package.swift": 25.0},
    depends=((re.compile(r"\\bswift(?:lang)?\\b", re.I), 12.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
)
''')

    w("typescript", HEADER.format(title="TypeScript", name="typescript") + '''
def _puff(tmpl: Path, stem: str, pascal: str) -> list[Path]:
    return merge_puff(puff_paths(tmpl, stem, "src/{stem}.ts", "src/{stem}.sh.in", "docs/{stem}.adoc", "{stem}.bash", "po/{stem}.pot"))

def _spec_files(puffs: list[str]) -> list[str]:
    p = puffs[0] if puffs else "zephyr"
    return ["%{_datadir}/%{name}/", f"%{{_infodir}}/{p}.info*"]

SPEC = LangSpec(
    name=NAME,
    ext_weights={".ts": 4.0, ".tsx": 4.0, ".cts": 3.0, ".mts": 3.0, ".js": 0.35, ".mjs": 0.35, ".cjs": 0.35},
    name_weights={"package.json": 10.0, "tsconfig.json": 25.0, "pnpm-lock.yaml": 5.0, "package-lock.json": 5.0, "yarn.lock": 5.0},
    shebangs=((re.compile(r"^#!.*\\bnode\\b"), 1.5),),
    depends=((re.compile(r"\\b(nodejs|npm|node-typescript|typescript)\\b", re.I), 10.0),),
    wire=WireSpec(kind="none", man=True),
    puff_fn=_puff,
    spec_files_fn=_spec_files,
)
''')

if __name__ == "__main__":
    main()
