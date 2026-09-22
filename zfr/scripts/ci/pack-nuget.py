#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pack a staged Windows install tree into a NuGet (.nupkg) package.

Usage:
  pack-nuget.py --id NAME --version VER --stage DIR --out FILE.nupkg
                [--rid win-x64|win-arm64] [--authors TEXT] [--description TEXT]
"""
from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


def _rel_files(stage: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(stage.rglob("*")):
        if p.is_file():
            files.append(p)
    return files


def _nuspec(
    *,
    pkg_id: str,
    version: str,
    authors: str,
    description: str,
) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">\n'
        "  <metadata>\n"
        f"    <id>{escape(pkg_id)}</id>\n"
        f"    <version>{escape(version)}</version>\n"
        f"    <authors>{escape(authors)}</authors>\n"
        f"    <description>{escape(description)}</description>\n"
        "  </metadata>\n"
        "</package>\n"
    )


def _content_types() -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Default Extension="nuspec" ContentType="application/octet"/>\n'
        '  <Default Extension="dll" ContentType="application/octet"/>\n'
        '  <Default Extension="exe" ContentType="application/octet"/>\n'
        '  <Default Extension="a" ContentType="application/octet"/>\n'
        '  <Default Extension="lib" ContentType="application/octet"/>\n'
        '  <Default Extension="h" ContentType="text/plain"/>\n'
        '  <Default Extension="pc" ContentType="text/plain"/>\n'
        '  <Default Extension="txt" ContentType="text/plain"/>\n'
        '  <Default Extension="md" ContentType="text/plain"/>\n'
        "</Types>\n"
    )


def _rels(pkg_id: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Type="http://schemas.microsoft.com/packaging/2010/07/'
        f'relationships/manifest" Target="/{pkg_id}.nuspec" Id="R1"/>\n'
        "</Relationships>\n"
    )


def pack(
    *,
    pkg_id: str,
    version: str,
    stage: Path,
    out: Path,
    authors: str,
    description: str,
    rid: str,
) -> Path:
    files = _rel_files(stage)
    if not files:
        raise SystemExit(f"pack-nuget: empty stage {stage}")

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types())
        zf.writestr("_rels/.rels", _rels(pkg_id))
        zf.writestr(
            f"{pkg_id}.nuspec",
            _nuspec(
                pkg_id=pkg_id,
                version=version,
                authors=authors,
                description=description,
            ),
        )
        for src in files:
            rel = src.relative_to(stage).as_posix()
            arc = f"runtimes/{rid}/native/{rel}"
            zf.write(src, arcname=arc)

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(
        f"pack-nuget: wrote {out} ({out.stat().st_size} bytes, "
        f"rid={rid}, sha256={digest[:16]}…)"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--id", required=True, help="NuGet package id")
    ap.add_argument("--version", required=True)
    ap.add_argument("--stage", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--rid", default="win-x64", help="NuGet RID (win-x64|win-arm64)")
    ap.add_argument("--authors", default="lenik")
    ap.add_argument("--description", default="")
    args = ap.parse_args()
    desc = args.description or f"{args.id} Windows native ({args.rid})"
    pack(
        pkg_id=args.id,
        version=args.version,
        stage=args.stage,
        out=args.out,
        authors=args.authors,
        description=desc,
        rid=args.rid,
    )


if __name__ == "__main__":
    main()
