# SPDX-License-Identifier: AGPL-3.0-or-later
"""groff man → AsciiDoc conversion."""
from __future__ import annotations

from .util import *  # noqa: F403

def strip_install_man_paths(text: str, remove: set[str]) -> str:
    """Drop groff (or adoc) paths from install_man() after conversion to docs/*.adoc.

    Meson install_man() only accepts numeric-section man sources, not AsciiDoc.
    """
    drop = set(remove)
    drop |= {p.replace("\\", "/") for p in remove}

    def _keep(name: str) -> bool:
        n = name.replace("\\", "/")
        if n in drop or Path(n).name in drop:
            return False
        if n.endswith(".adoc") or n.endswith(".adoc.in"):
            return False
        return True

    def repl(m: re.Match[str]) -> str:
        inner = m.group(1)
        names = [a or b for a, b in re.findall(r"'([^']+)'|\"([^\"]+)\"", inner)]
        kept = [n for n in names if _keep(n)]
        if not kept:
            return ""
        if len(kept) == 1:
            return f"install_man('{kept[0]}')\n"
        files = ", ".join(f"'{k}'" for k in kept)
        return f"install_man([{files}])\n"

    return re.sub(r"install_man\s*\(([^)]*)\)[ \t]*\n?", repl, text)


def _man_target(name: str, section: str = "1") -> str:
    return f"""
custom_target(
    '{name}-man',
    input: 'docs/{name}.adoc',
    output: '{name}.{section}',
    command: [
        asciidoctor,
        '-b', 'manpage',
        '-a', 'project-version=' + meson.project_version(),
        '-a', 'project-year=@0@'.format(project_year),
        '-a', 'project-author=' + project_author,
        '-a', 'project-email=' + project_email,
        '-o', '@OUTPUT@',
        '@INPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: mandir / 'man{section}',
)
"""


_INDIVIDUAL_MAN_TARGET_RE = re.compile(
    r"\ncustom_target\(\s*"
    r"'(?P<stem>[^']+)-man'\s*,\s*"
    r"input:\s*'docs/(?P=stem)\.adoc'\s*,"
    r".*?"
    r"install_dir:\s*mandir\s*/\s*'man[^']+'\s*,\s*"
    r"\)\s*",
    re.DOTALL,
)


def has_foreach_man_targets(text: str) -> bool:
    """True when meson already builds mans via ``foreach`` (e.g. ``puff + '-man'``)."""
    if not re.search(r"\bforeach\b", text):
        return False
    # Expression-style target names: puff + '-man' / name + "-man"
    if re.search(r"""\+\s*['"]-man['"]""", text):
        return True
    # foreach over a list that feeds asciidoctor manpage custom_targets
    if re.search(
        r"foreach\b.*?custom_target\s*\(.*?['\"]manpage['\"]",
        text,
        re.DOTALL | re.IGNORECASE,
    ):
        return True
    return False


def strip_individual_man_targets(text: str) -> tuple[str, list[str]]:
    """Remove per-stem ``custom_target('foo-man', …)`` blocks ize used to append."""
    removed: list[str] = []

    def _repl(m: re.Match[str]) -> str:
        removed.append(m.group("stem"))
        return "\n"

    new = _INDIVIDUAL_MAN_TARGET_RE.sub(_repl, text)
    return new, removed


def man_foreach_block(stems: list[str], *, section: str = "1") -> str:
    """Meson ``foreach`` over English docs/*.adoc man pages (zephyr style)."""
    if not stems:
        return ""
    quoted = ",\n    ".join(f"'{s}'" for s in stems)
    return f"""
man_puffs = [
    {quoted},
]
foreach puff : man_puffs
  custom_target(
    puff + '-man',
    input: 'docs' / (puff + '.adoc'),
    output: puff + '.{section}',
    command: [
      asciidoctor,
      '-b', 'manpage',
      '-a', 'project-version=' + meson.project_version(),
      '-a', 'project-year=@0@'.format(project_year),
      '-a', 'project-author=' + project_author,
      '-a', 'project-email=' + project_email,
      '-o', '@OUTPUT@',
      '@INPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: mandir / 'man{section}',
  )
endforeach
"""


def ensure_meson_man_targets(text: str, stems: list[str], *, section: str = "1") -> tuple[str, list[str]]:
    """Ensure English man custom_targets exist; prefer foreach, never duplicate.

    If meson already has a foreach-based man loop, drop leftover individual
    ``'stem-man'`` targets and do not append more. Otherwise add a single
    ``man_puffs`` foreach for missing stems (or refresh the list).
    """
    details: list[str] = []
    if has_foreach_man_targets(text):
        cleaned, removed = strip_individual_man_targets(text)
        if removed:
            details.append(
                "remove duplicate individual man targets: " + ", ".join(removed)
            )
        return cleaned, details

    missing = [
        s
        for s in stems
        if f"'{s}-man'" not in text and f'"{s}-man"' not in text
    ]
    if not missing:
        return text, details

    # Prefer one foreach for all English docs mans.
    all_stems = sorted(set(stems))
    block = man_foreach_block(all_stems, section=section)
    # Drop any individual targets we're about to cover via foreach.
    text, removed = strip_individual_man_targets(text)
    if removed:
        details.append("fold individual man targets into foreach")
    text = text.rstrip() + "\n" + block
    details.append(f"man foreach ({len(all_stems)} puffs)")
    return text, details


def groff_to_adoc(text: str, name: str, section: str = "1") -> str:
    """Best-effort groff man → AsciiDoc (used when pandoc is unavailable)."""
    body: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith('.\\"') or line.startswith("'\\\""):
            continue
        if line.startswith(".TH"):
            continue
        m = re.match(r"^\.SH\s+(.*)$", line, re.I)
        if m:
            title = m.group(1).strip().strip('"')
            body.append("")
            body.append(f"== {title.title() if title.isupper() else title}")
            body.append("")
            continue
        if line.startswith(".SS"):
            title = line[3:].strip().strip('"')
            body.append("")
            body.append(f"=== {title}")
            body.append("")
            continue
        if line in (".PP", ".P", ".LP", ".br"):
            body.append("")
            continue
        if line.startswith(".TP"):
            body.append("")
            continue
        line = re.sub(r"\\fB(.*?)\\f[PR]", r"*\1*", line)
        line = re.sub(r"\\fI(.*?)\\f[PR]", r"_\1_", line)
        line = line.replace("\\-", "-").replace("\\&", "")
        if line.startswith("."):
            continue
        body.append(line)
    inner = "\n".join(body).strip() or f"{name} command."
    return (
        f"= {name}({section})\n"
        "{project-author} <{project-email}>\n"
        "v{project-version}, {project-year}\n"
        ":doctype: manpage\n"
        ":manmanual: User Commands\n"
        f":mansource: {name}\n"
        ":man-linkstyle: blue R <>\n"
        ":nofooter:\n"
        "\n"
        f"{inner}\n"
        "\n"
        "== Author\n"
        "\n"
        "Written by {project-author} <{project-email}>.\n"
        "\n"
        "== Copyright\n"
        "\n"
        "Copyright (C) {project-year}.\n"
        f"License {_AGPL}.\n"
    )


def convert_man_file(path: Path, name: str, section: str = "1") -> str:
    if shutil.which("pandoc"):
        proc = subprocess.run(
            ["pandoc", "-f", "man", "-t", "asciidoc", "--wrap=none", str(path)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            body = proc.stdout.strip()
            if not body.lstrip().startswith("= "):
                body = f"= {name}({section})\n\n{body}"
            header = (
                "{project-author} <{project-email}>\n"
                "v{project-version}, {project-year}\n"
                ":doctype: manpage\n"
                ":manmanual: User Commands\n"
                f":mansource: {name}\n"
                ":man-linkstyle: blue R <>\n"
                ":nofooter:\n"
            )
            if ":doctype: manpage" not in body:
                parts = body.split("\n", 1)
                body = parts[0] + "\n" + header + (parts[1] if len(parts) > 1 else "")
            return body if body.endswith("\n") else body + "\n"
    return groff_to_adoc(path.read_text(encoding="utf-8", errors="ignore"), name, section)


def stub_man_adoc(name: str, section: str = "1", summary: str = "") -> str:
    """Minimal AsciiDoc man page so layout.docs / asciidoctor targets pass lint."""
    desc = summary.strip() or f"{name} command"
    return (
        f"= {name}({section})\n"
        "{project-author} <{project-email}>\n"
        "v{project-version}, {project-year}\n"
        ":doctype: manpage\n"
        ":manmanual: User Commands\n"
        f":mansource: {name}\n"
        ":man-linkstyle: blue R <>\n"
        ":nofooter:\n"
        "\n"
        "== Name\n"
        "\n"
        f"{name} - {desc}\n"
        "\n"
        "== Synopsis\n"
        "\n"
        f"*{name}* [_OPTION_]...\n"
        "\n"
        "== Description\n"
        "\n"
        f"{desc}.\n"
        "\n"
        "== Options\n"
        "\n"
        "*-h, --help*::\n"
        "  Show a short usage summary and exit.\n"
        "\n"
        "== Author\n"
        "\n"
        "Written by {project-author} <{project-email}>.\n"
        "\n"
        "== Copyright\n"
        "\n"
        "Copyright (C) {project-year}.\n"
        f"License {_AGPL}.\n"
    )


def discover_man_stems(root: Path, project: str) -> list[tuple[str, str]]:
    """Guess (stem, section) pairs for man pages from Autotools / Meson traces."""
    found: dict[str, str] = {}

    def add(stem: str, section: str = "1") -> None:
        stem = Path(stem).name
        if not stem or stem.startswith("."):
            return
        found.setdefault(stem, section)

    # Existing AsciiDoc already covered.
    docs = root / "docs"
    if docs.is_dir():
        for p in docs.glob("*.adoc"):
            add(p.stem, "1")

    # help2man / install_man leftovers in meson.build
    meson = root / "meson.build"
    if meson.is_file():
        text = meson.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"output:\s*'([^']+\.[1-9][a-zA-Z]*)'", text):
            name = Path(m.group(1)).name
            stem, _, sec = name.rpartition(".")
            if stem:
                add(stem, sec or "1")
        for m in re.finditer(r"install_man\s*\(([^)]*)\)", text):
            for q in re.findall(r"'([^']+)'|\"([^\"]+)\"", m.group(1)):
                name = Path(q[0] or q[1]).name
                if re.search(r"\.[1-9][a-zA-Z]*$", name):
                    stem, _, sec = name.rpartition(".")
                    add(stem, sec)

    # Makefile.am man_MANS / dist_man_MANS
    for am in root.rglob("Makefile.am"):
        try:
            am_text = am.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(
            r"^(?:dist_|notrans_)?man_MANS\s*[+?:]?=\s*(.*(?:\\\n.*)*)",
            am_text,
            re.M,
        ):
            words = re.sub(r"\\\n", " ", m.group(1))
            for w in words.split():
                w = w.strip()
                if re.search(r"\.[1-9][a-zA-Z]*$", w):
                    stem, _, sec = Path(w).name.rpartition(".")
                    add(stem, sec)

    if not found:
        add(project, "1")
    # Prefer stems that do not yet have docs/*.adoc when returning for stub creation.
    return sorted(found.items())


def strip_help2man_blocks(text: str) -> str:
    """Remove help2man find_program + if/endif custom_target blocks from meson.build."""
    if "help2man" not in text:
        return text
    # Drop: help2man = find_program(...) and following if help2man.found() ... endif
    text2 = re.sub(
        r"\n?#?\s*help2man\s*=\s*find_program\([^)]*\)\s*\n"
        r"if\s+help2man\.found\(\)\s*\n"
        r"(?:.*?\n)*?endif\s*\n?",
        "\n",
        text,
        flags=re.S,
    )
    return text2

