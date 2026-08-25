# SPDX-License-Identifier: AGPL-3.0-or-later
"""Patch debian/control to satisfy zfr lint after mesonize."""
from __future__ import annotations

import re

REQUIRED_BUILD_DEPENDS = ("meson", "ninja-build", "asciidoctor")


def _field_packages(block: str) -> set[str]:
    """Package names mentioned in a Depends/Build-Depends body."""
    names: set[str] = set()
    for part in re.split(r"[,|\n]", block):
        tok = part.strip().split()[0] if part.strip() else ""
        tok = tok.split("(")[0].strip()
        if tok and not tok.startswith("${"):
            names.add(tok)
    return names


def ensure_build_depends(text: str, extras: tuple[str, ...] = REQUIRED_BUILD_DEPENDS) -> tuple[str, list[str]]:
    """Ensure Source Build-Depends lists *extras*. Returns (text, change notes)."""
    notes: list[str] = []
    m = re.search(
        r"^(Build-Depends:\s*)(.*?)(?=\n[A-Za-z][\w-]*:|\Z)",
        text,
        re.S | re.M,
    )
    if not m:
        return text, notes
    body = m.group(2)
    have = _field_packages(body)
    missing = [e for e in extras if e not in have]
    if not missing:
        return text, notes
    # Prefer multi-line style when already multi-line or body is long.
    if "\n" in body.rstrip() or len(body) > 40:
        indent = " "
        stripped = body.rstrip()
        if stripped and not stripped.endswith(","):
            stripped += ","
        addition = "".join(f"\n{indent}{e}," for e in missing)
        addition = addition.rstrip(",")
        new_body = stripped + addition + "\n"
    else:
        new_body = body.rstrip()
        if new_body and not new_body.endswith(","):
            new_body += ","
        new_body += " " + ", ".join(missing)
        # Keep a trailing newline so the next Debian field stays on its own line.
        new_body += "\n"
    notes.append("Build-Depends +" + ", ".join(missing))
    return text[: m.start(2)] + new_body + text[m.end(2) :], notes


def ensure_architecture(text: str, *, lang: str) -> tuple[str, list[str]]:
    """Ensure the first Package stanza has Architecture."""
    notes: list[str] = []
    want = "all" if lang == "bash" else "any"
    # Split on blank lines into stanzas.
    parts = re.split(r"\n(?=Package:\s)", text, maxsplit=1)
    if len(parts) < 2:
        # No Package stanza yet — nothing to fix.
        return text, notes
    head, pkg = parts[0], parts[1]
    if re.search(r"^Architecture:\s*\S", pkg, re.M):
        return text, notes
    # Insert after Package: line.
    pkg2, n = re.subn(
        r"^(Package:\s*\S+[^\n]*\n)",
        rf"\1Architecture: {want}\n",
        pkg,
        count=1,
        flags=re.M,
    )
    if n:
        notes.append(f"Architecture: {want}")
        if not head.endswith("\n"):
            head += "\n"
        return head + pkg2, notes
    return text, notes


def ensure_bash_shlib_depends(text: str) -> tuple[str, list[str]]:
    """Ensure Package Depends includes bash-shlib for bash projects."""
    notes: list[str] = []
    parts = re.split(r"\n(?=Package:\s)", text, maxsplit=1)
    if len(parts) < 2:
        return text, notes
    head, pkg = parts[0], parts[1]
    m = re.search(
        r"^(Depends:\s*)(.*?)(?=\n[A-Za-z][\w-]*:|\Z)",
        pkg,
        re.S | re.M,
    )
    if not m:
        # Insert Depends after Architecture or Package.
        pkg2, n = re.subn(
            r"^(Architecture:\s*\S+[^\n]*\n)",
            r"\1Depends: bash, bash-shlib, ${misc:Depends}\n",
            pkg,
            count=1,
            flags=re.M,
        )
        if not n:
            pkg2, n = re.subn(
                r"^(Package:\s*\S+[^\n]*\n)",
                r"\1Depends: bash, bash-shlib, ${misc:Depends}\n",
                pkg,
                count=1,
                flags=re.M,
            )
        if n:
            notes.append("Depends: bash-shlib")
            if not head.endswith("\n"):
                head += "\n"
            return head + pkg2, notes
        return text, notes
    body = m.group(2)
    if "bash-shlib" in _field_packages(body):
        return text, notes
    stripped = body.rstrip()
    if "\n" in stripped:
        if stripped and not stripped.endswith(","):
            stripped += ","
        new_body = stripped + "\n bash-shlib,\n"
    else:
        new_body = stripped
        if new_body and not new_body.endswith(","):
            new_body += ","
        new_body += " bash-shlib"
        if body.endswith("\n"):
            new_body += "\n"
    notes.append("Depends: bash-shlib")
    pkg2 = pkg[: m.start(2)] + new_body + pkg[m.end(2) :]
    if not head.endswith("\n"):
        head += "\n"
    return head + pkg2, notes


def normalize_control_blank_lines(text: str) -> str:
    """Keep blank lines only between stanzas; drop blanks inside a stanza.

    Autotools-era controls often put a blank line after Build-Depends before
    Standards-Version, which splits the Source stanza.  Likewise a blank line
    before Description splits Package.  Lint (and dpkg) expect one stanza per
    blank-line-separated block.
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            # Peek: keep a blank only when the next non-empty line starts a stanza.
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and re.match(r"^(Source|Package)\s*:", lines[j]):
                if out and out[-1] != "":
                    out.append("")
            i = j
            continue
        out.append(line)
        i += 1
    body = "\n".join(out).strip() + "\n"
    # Ensure a blank line before every Package: that follows other content.
    body = re.sub(r"([^\n])\n(Package\s*:)", r"\1\n\n\2", body)
    return body


def patch_debian_control(text: str, *, lang: str) -> tuple[str, list[str]]:
    """Apply all debian/control fixes for *lang*. Returns (new_text, notes)."""
    notes: list[str] = []
    normalized = normalize_control_blank_lines(text)
    if normalized != text:
        notes.append("normalize blank lines")
        text = normalized
    text, n = ensure_build_depends(text)
    notes.extend(n)
    text, n = ensure_architecture(text, lang=lang)
    notes.extend(n)
    if lang == "bash":
        text, n = ensure_bash_shlib_depends(text)
        notes.extend(n)
    # Re-normalize in case inserts disturbed stanza spacing.
    text2 = normalize_control_blank_lines(text)
    if text2 != text:
        text = text2
    return text, notes


def strip_readme_banner(text: str, name: str) -> str:
    """Remove template placeholder banners and retitle for *name*."""
    lines = text.splitlines()
    # Drop leading banner paragraphs (EN + ZH markers).
    markers = (
        "THIS FILE IS GENERATED FROM A TEMPLATE",
        "本文件由模板生成",
    )
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if not ln:
            i += 1
            continue
        if any(m in ln for m in markers) or ln.startswith("Except for the project") or ln.startswith(
            "除项目名称"
        ) or ln.startswith("Please rewrite") or ln.startswith("请根据"):
            i += 1
            continue
        break
    body = "\n".join(lines[i:]).lstrip("\n")
    # Replace common template titles.
    body = re.sub(r"(?m)^#\s+zephyr\s*$", f"# {name}", body, count=1)
    body = re.sub(r"(?m)^#\s+zephyr\s*$", f"# {name}", body, count=1)
    body = body.replace("`zephyr`", f"`{name}`")
    body = body.replace("zephyr", name)
    if not body.strip():
        body = (
            f"# {name}\n\n"
            f"`{name}` — converted to Meson / zephyr packaging style.\n\n"
            "## Build\n\n"
            "```bash\n"
            "meson setup build && ninja -C build\n"
            "```\n"
        )
    return body if body.endswith("\n") else body + "\n"


def ensure_rpm_bash_shlib(spec_text: str) -> tuple[str, bool]:
    """Add Requires: bash-shlib when missing."""
    if re.search(r"(?mi)^Requires:.*\bbash-shlib\b", spec_text):
        return spec_text, False
    if re.search(r"(?mi)^Requires:", spec_text):
        new, n = re.subn(
            r"(?mi)^(Requires:\s*)(.*)$",
            lambda m: m.group(0)
            if "bash-shlib" in m.group(2)
            else f"{m.group(1)}{m.group(2).rstrip()}, bash-shlib",
            spec_text,
            count=1,
        )
        if n:
            return new, True
    # Insert after BuildRequires block / Name.
    m = re.search(r"(?mi)^BuildRequires:.*(?:\nBuildRequires:.*)*\n", spec_text)
    if m:
        insert = m.end()
        return spec_text[:insert] + "Requires:       bash-shlib\n" + spec_text[insert:], True
    m = re.search(r"(?mi)^Name:\s*.*\n", spec_text)
    if m:
        return (
            spec_text[: m.end()] + "Requires:       bash-shlib\n" + spec_text[m.end() :],
            True,
        )
    return spec_text + "\nRequires:       bash-shlib\n", True
