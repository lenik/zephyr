# SPDX-License-Identifier: AGPL-3.0-or-later
"""groff man → AsciiDoc conversion."""
from __future__ import annotations

from .util import *  # noqa: F403

def _man_target(name: str) -> str:
    return f"""
custom_target(
    '{name}-man',
    input: 'docs/{name}.adoc',
    output: '{name}.1',
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
    install_dir: mandir / 'man1',
)
"""


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


def convert_man_file(path: Path, name: str) -> str:
    if shutil.which("pandoc"):
        proc = subprocess.run(
            ["pandoc", "-f", "man", "-t", "asciidoc", "--wrap=none", str(path)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            body = proc.stdout.strip()
            if not body.lstrip().startswith("= "):
                body = f"= {name}(1)\n\n{body}"
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
    return groff_to_adoc(path.read_text(encoding="utf-8", errors="ignore"), name)
