# SPDX-License-Identifier: AGPL-3.0-or-later
"""zfr about — project summary for the console (and AI coders)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from . import (
    _is_zfr_meta_repo,
    detect_lang,
    find_project_dir,
    is_probably_text,
    iter_files,
    project_version,
    rpm_compatible_version,
)
from .commands import _meson_project_fields, _parse_control_stanzas
from .csr import Csr, human_size, render_fields, split_commas, term_columns, wrap_text

_LIST_KEYS = frozenset(
    {
        "Build-Depends",
        "Depends",
        "Recommends",
        "Suggests",
        "BuildRequires",
        "Requires",
        "Provides",
        "Obsoletes",
        "Conflicts",
    }
)

_SOURCE_EXT = {
    ".c",
    ".h",
    ".cc",
    ".cpp",
    ".cxx",
    ".hpp",
    ".hh",
    ".rs",
    ".go",
    ".py",
    ".pl",
    ".pm",
    ".rb",
    ".java",
    ".ts",
    ".js",
    ".cs",
    ".hs",
    ".erl",
    ".hrl",
    ".st",
    ".swift",
    ".sh",
    ".bash",
    ".in",
    ".adoc",
}

_SOURCE_NAMES = {
    "meson.build",
    "meson.options",
    "meson_options.txt",
    "Cargo.toml",
    "go.mod",
    "package.json",
}

_SOURCE_DIRS = {"src", "cmd", "apps", "lib", "tests", "tools"}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _specs(root: Path) -> list[Path]:
    found: list[Path] = []
    rpm = root / "rpm"
    if rpm.is_dir():
        found.extend(sorted(rpm.glob("*.spec")))
    found.extend(sorted(root.glob("*.spec")))
    uniq: list[Path] = []
    seen: set[Path] = set()
    for p in found:
        r = p.resolve()
        if r in seen:
            continue
        seen.add(r)
        uniq.append(p)
    return uniq


def _parse_changelog(root: Path) -> dict[str, str]:
    path = root / "debian" / "changelog"
    text = _read(path)
    out: dict[str, str] = {}
    if not text:
        return out
    m = re.match(
        r"^(\S+)\s+\(([^)]+)\)\s+([^;]+);\s*urgency=(\S+)",
        text,
        re.M,
    )
    if m:
        out["Source"] = m.group(1)
        out["Version"] = m.group(2).split(":", 1)[-1]
        out["Distribution"] = m.group(3).strip()
        out["Urgency"] = m.group(4).rstrip(".")
    trailer = None
    for line in text.splitlines():
        if line.startswith(" -- "):
            trailer = line[4:].strip()
            break
    if trailer:
        tm = re.match(r"(.+>)\s\s+(.+)", trailer)
        if tm:
            out["Changed-By"] = tm.group(1).strip()
            out["Date"] = tm.group(2).strip()
        else:
            out["Changed-By"] = trailer
    return out


def _parse_spec(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    for key in (
        "Name",
        "Version",
        "Release",
        "Summary",
        "License",
        "URL",
        "Packager",
        "Group",
        "BuildArch",
        "BuildRequires",
        "Requires",
        "Provides",
        "Source0",
        "Source",
    ):
        vals = [v.strip() for v in re.findall(rf"^{re.escape(key)}\s*:\s*(.+)$", text, re.M)]
        if not vals:
            continue
        if key in ("BuildRequires", "Requires", "Provides") or len(vals) > 1:
            lists[key] = vals
            out[key] = ", ".join(vals)
        else:
            out[key] = vals[0]
    m = re.search(r"^%description\s*\n(.*?)(?=^%\w)", text, re.M | re.S)
    if m:
        body = m.group(1).strip()
        if body:
            out["Description"] = re.sub(r"\n{3,}", "\n\n", body)
    return out


def _debian(root: Path) -> tuple[dict[str, str], dict[str, str], str]:
    path = root / "debian" / "control"
    text = _read(path)
    stanzas = _parse_control_stanzas(text) if text else []
    src = stanzas[0] if stanzas else {}
    pkg = stanzas[1] if len(stanzas) > 1 else src
    return src, pkg, text


def _flatten_list(val: str) -> str:
    return ", ".join(split_commas(val))


def _description_parts(desc: str) -> tuple[str, str]:
    if not desc:
        return "", ""
    summary, _, rest = desc.partition("\n")
    paras: list[str] = []
    buf: list[str] = []
    for line in rest.splitlines():
        if line.strip() in {".", ""}:
            if buf:
                paras.append(" ".join(buf))
                buf = []
            continue
        buf.append(line.strip())
    if buf:
        paras.append(" ".join(buf))
    return summary.strip(), "\n\n".join(paras)


def _is_packaging_artifact(root: Path, rel: Path) -> bool:
    parts = rel.parts
    if not parts:
        return False
    if parts[0] in {"rpmbuild", "build", "dist"}:
        return True
    if parts[0] != "debian" or len(parts) < 2:
        return False
    second = parts[1]
    if second in {"files", "debhelper-build-stamp"}:
        return True
    if second.endswith(".substvars") or second.endswith(".debhelper"):
        return True
    dest = root / "debian" / second
    if dest.is_dir() and ((dest / "DEBIAN").is_dir() or (dest / "usr").is_dir()):
        return True
    return False


def _is_source(rel: Path) -> bool:
    if rel.name in _SOURCE_NAMES or rel.suffix.lower() in _SOURCE_EXT:
        return True
    return bool(rel.parts and rel.parts[0] in _SOURCE_DIRS)


def _count_lines(path: Path) -> int:
    try:
        data = path.read_bytes()
    except OSError:
        return 0
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def _project_stats(root: Path, lang: str) -> dict[str, str]:
    source_files = 0
    source_lines = 0
    source_bytes = 0
    tree_files = 0
    tree_bytes = 0
    payload_bytes = 0
    by_ext: dict[str, int] = {}

    for path in iter_files(root):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if _is_packaging_artifact(root, rel):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        tree_files += 1
        tree_bytes += size

        payload = False
        if rel.parts and rel.parts[0] in {"src", "docs", "po"}:
            payload = True
        elif rel.name in {"LICENSE", "README.md", "README-zh.md"}:
            payload = True
        elif rel.suffix == ".bash" and len(rel.parts) == 1:
            payload = True
        elif _is_zfr_meta_repo(root) and rel.parts and rel.parts[0] not in {"debian", "rpm"}:
            payload = True
        if payload:
            payload_bytes += size

        if not _is_source(rel):
            continue
        if not is_probably_text(path):
            continue
        source_files += 1
        source_bytes += size
        source_lines += _count_lines(path)
        label = "meson" if rel.name == "meson.build" else (rel.suffix.lower().lstrip(".") or rel.name)
        by_ext[label] = by_ext.get(label, 0) + 1

    top_ext = sorted(by_ext.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    mix = ", ".join(f"{n} {ext}" if n != 1 else ext for ext, n in top_ext) if top_ext else lang

    return {
        "Sources": f"{source_files} files, {source_lines} lines ({mix})",
        "Tree": f"{tree_files} files, {human_size(tree_bytes)}",
        "Package": f"~{human_size(payload_bytes)} payload (est.)",
        "Source-bytes": str(source_bytes),
    }


def _common_rows(
    *,
    name: str,
    lang: str,
    root: Path,
    version: str,
    meson: dict[str, str],
    src: dict[str, str],
    pkg: dict[str, str],
    spec: dict[str, str],
    changelog: dict[str, str],
    summary: str,
) -> list[tuple[str, str]]:
    license_ = meson.get("license") or spec.get("License") or ""
    homepage = src.get("Homepage") or spec.get("URL") or ""
    maintainer = src.get("Maintainer") or spec.get("Packager") or ""
    section = src.get("Section") or spec.get("Group") or ""
    priority = src.get("Priority") or ""
    dist = changelog.get("Distribution") or ""
    arch = pkg.get("Architecture") or spec.get("BuildArch") or ""
    stats = _project_stats(root, lang)
    return [
        ("Name", name),
        ("Language", lang),
        ("Directory", str(root)),
        ("Version", version),
        ("License", license_),
        ("Homepage", homepage),
        ("Maintainer", maintainer),
        ("Summary", summary),
        ("Section", section),
        ("Priority", priority),
        ("Distribution", dist),
        ("Architecture", arch),
        ("Sources", stats["Sources"]),
        ("Tree", stats["Tree"]),
        ("Package", stats["Package"]),
    ]


def _debian_rows(
    src: dict[str, str],
    pkg: dict[str, str],
    changelog: dict[str, str],
    summary: str,
) -> list[tuple[str, str]]:
    return [
        ("Source", src.get("Source") or ""),
        ("Package", pkg.get("Package") or ""),
        ("Section", src.get("Section") or ""),
        ("Priority", src.get("Priority") or ""),
        ("Architecture", pkg.get("Architecture") or ""),
        ("Maintainer", src.get("Maintainer") or ""),
        ("Standards", src.get("Standards-Version") or ""),
        ("Homepage", src.get("Homepage") or ""),
        ("Rules-Requires-Root", src.get("Rules-Requires-Root") or ""),
        ("Build-Depends", _flatten_list(src.get("Build-Depends") or "")),
        ("Depends", _flatten_list(pkg.get("Depends") or "")),
        ("Recommends", _flatten_list(pkg.get("Recommends") or "")),
        ("Suggests", _flatten_list(pkg.get("Suggests") or "")),
        ("Summary", summary),
        ("Changelog-Version", changelog.get("Version") or ""),
        ("Distribution", changelog.get("Distribution") or ""),
        ("Urgency", changelog.get("Urgency") or ""),
        ("Date", changelog.get("Date") or ""),
        ("Changed-By", changelog.get("Changed-By") or ""),
    ]


def _rpm_rows(root: Path, spec_path: Path, spec: dict[str, str], version: str) -> list[tuple[str, str]]:
    try:
        rel = str(spec_path.relative_to(root))
    except ValueError:
        rel = str(spec_path)
    ver = spec.get("Version") or ""
    if "%{" in ver or not ver:
        ver = f"{rpm_compatible_version(version)}  (from zfr version)"
    return [
        ("Spec", rel),
        ("Name", spec.get("Name") or ""),
        ("Version", ver),
        ("Release", spec.get("Release") or ""),
        ("Summary", spec.get("Summary") or ""),
        ("License", spec.get("License") or ""),
        ("URL", spec.get("URL") or ""),
        ("Packager", spec.get("Packager") or ""),
        ("Group", spec.get("Group") or ""),
        ("BuildArch", spec.get("BuildArch") or ""),
        ("BuildRequires", spec.get("BuildRequires") or ""),
        ("Requires", spec.get("Requires") or ""),
        ("Provides", spec.get("Provides") or ""),
        ("Source", spec.get("Source0") or spec.get("Source") or ""),
    ]


def _write_paragraphs(title: str, body: str, *, csr: Csr, columns: int) -> None:
    if not body.strip():
        return
    sys.stdout.write("\n")
    sys.stdout.write(csr.wrap(title, csr.bold, csr.cyan) + "\n")
    value_w = max(16, columns - 2)
    for para in re.split(r"\n\s*\n", body.strip()):
        for line in wrap_text(para, value_w):
            sys.stdout.write(f"  {line}\n")
        sys.stdout.write("\n")


def cmd_about(
    *,
    debian: bool = False,
    redhat: bool = False,
    color: str = "auto",
    workdir: Path | None = None,
) -> None:
    """Print information about the current project (walks parents from cwd)."""
    root = find_project_dir(workdir)
    meson = _meson_project_fields(root)
    src, pkg, control_txt = _debian(root)
    changelog = _parse_changelog(root)
    specs = _specs(root)
    spec_path = specs[0] if specs else None
    spec = _parse_spec(_read(spec_path)) if spec_path else {}

    name = src.get("Source") or spec.get("Name") or meson.get("name") or root.name
    if _is_zfr_meta_repo(root):
        lang = "meta"
    else:
        try:
            lang = detect_lang(root)
        except SystemExit:
            lang = "unknown"

    desc = pkg.get("Description") or spec.get("Description") or ""
    summary, long_desc = _description_parts(desc)
    if not summary:
        summary = spec.get("Summary") or ""
    version = project_version(root)

    csr = Csr(color)
    cols = term_columns()
    head = csr.wrap("zfr about", csr.bold)
    sys.stdout.write(f"{head}  {csr.wrap(str(root), csr.dim)}\n")

    common = _common_rows(
        name=name,
        lang=lang,
        root=root,
        version=version,
        meson=meson,
        src=src,
        pkg=pkg,
        spec=spec,
        changelog=changelog,
        summary=summary,
    )
    sys.stdout.write(render_fields(common, csr=csr, columns=cols, list_keys=_LIST_KEYS))
    sys.stdout.write("\n")

    if debian:
        sys.stdout.write("\n")
        sys.stdout.write(csr.wrap("Debian", csr.bold, csr.magenta) + "\n")
        if not control_txt:
            sys.stdout.write(csr.wrap("(no debian/control)", csr.dim) + "\n")
        else:
            block = render_fields(
                _debian_rows(src, pkg, changelog, summary),
                csr=csr,
                columns=cols,
                list_keys=_LIST_KEYS,
            )
            sys.stdout.write(block + "\n")
            _write_paragraphs("Description", long_desc, csr=csr, columns=cols)

    if redhat:
        sys.stdout.write("\n")
        sys.stdout.write(csr.wrap("RPM", csr.bold, csr.magenta) + "\n")
        if not spec_path:
            sys.stdout.write(csr.wrap("(no .spec file)", csr.dim) + "\n")
        else:
            block = render_fields(
                _rpm_rows(root, spec_path, spec, version),
                csr=csr,
                columns=cols,
                list_keys=_LIST_KEYS,
            )
            sys.stdout.write(block + "\n")
            _write_paragraphs("Description", spec.get("Description") or "", csr=csr, columns=cols)

    sys.stdout.flush()
