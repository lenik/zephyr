# SPDX-License-Identifier: AGPL-3.0-or-later
"""Canonical standard files: LICENSE, .githooks, .cursor/rules, CI scaffold.

Installed by ``zfr create`` and reset by ``zfr ize``. Not part of language
templates. CI lives under ``share/ci`` (``.github/workflows`` + ``scripts/ci``).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from lib import pkgdatadir
from cursor_rules import RULE_NAMES, cursor_rule_src, install_cursor_rules


def license_src() -> Path | None:
    candidates = [
        pkgdatadir() / "LICENSE",
        pkgdatadir() / "std" / "LICENSE",
    ]
    here = Path(__file__).resolve()
    if here.parent.name == "src" and (here.parent / "zfr").is_file():
        candidates.append(here.parents[1] / "LICENSE")
    for path in candidates:
        if path.is_file():
            return path
    return None


def githooks_pre_commit_src() -> Path | None:
    # Project hook (debian/changelog at tree root). Never use the meta-repo
    # .githooks (that one points at zfr/debian).
    candidates = [
        pkgdatadir() / "githooks" / "pre-commit",
        pkgdatadir() / ".githooks" / "pre-commit",
    ]
    here = Path(__file__).resolve()
    if here.parent.name == "src" and (here.parent / "zfr").is_file():
        candidates.append(here.parents[1] / "githooks" / "pre-commit")
    for path in candidates:
        if path.is_file():
            return path
    return None


def install_license(dest: Path, *, project: str | None = None) -> Path | None:
    """Install LICENSE, substituting template ``zephyr`` tokens for *project*."""
    from lib import apply_name_replacements, instantiation_pairs

    src = license_src()
    if src is None:
        return None
    dest_file = dest / "LICENSE"
    text = src.read_text(encoding="utf-8")
    name = project or dest.name
    if name and name != "zephyr":
        text = apply_name_replacements(text, instantiation_pairs(name))
    dest_file.write_text(text, encoding="utf-8")
    try:
        shutil.copystat(src, dest_file)
    except OSError:
        pass
    return dest_file


def install_githooks(dest: Path) -> Path | None:
    src = githooks_pre_commit_src()
    if src is None:
        return None
    hook_dir = dest / ".githooks"
    dest_hook = hook_dir / "pre-commit"
    hook_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_hook)
    dest_hook.chmod(dest_hook.stat().st_mode | 0o111)
    return dest_hook


def ci_scaffold_src() -> Path | None:
    """Root of the shared GitHub Actions CI scaffold (share/ci)."""
    candidates: list[Path] = [
        pkgdatadir() / "ci",
        pkgdatadir() / "zfr" / "share" / "ci",
    ]
    here = Path(__file__).resolve()
    if here.parent.name == "src" and (here.parent / "zfr").is_file():
        candidates.append(here.parents[1] / "share" / "ci")
    for path in candidates:
        if (path / ".github" / "workflows" / "release-packages.yml").is_file():
            return path
    return None


def install_ci_scaffold(dest: Path) -> list[Path]:
    """Install/overwrite .github/workflows + scripts/ci from the zfr share."""
    src_root = ci_scaffold_src()
    if src_root is None:
        return []
    installed: list[Path] = []
    mapping = [
        (".github/workflows/release-packages.yml", 0o644),
        ("scripts/ci/matrix.json", 0o644),
        ("scripts/ci/matrix-from-json.sh", 0o755),
        ("scripts/ci/build-deb.sh", 0o755),
        ("scripts/ci/build-rpm.sh", 0o755),
        ("scripts/ci/publish-private.sh", 0o755),
        ("scripts/ci/fetch-dep.sh", 0o755),
        ("scripts/ci/deps.conf.example", 0o644),
    ]
    for rel, mode in mapping:
        src = src_root / rel
        if not src.is_file():
            continue
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        out.chmod(out.stat().st_mode | (0o111 if mode & 0o111 else 0))
        installed.append(out)
    return installed


def install_std_files(dest: Path, *, project: str | None = None) -> list[Path]:
    """Install/overwrite LICENSE, .githooks/pre-commit, cursor rules, and CI scaffold."""
    installed: list[Path] = []
    lic = install_license(dest, project=project or dest.name)
    if lic is not None:
        installed.append(lic)
    for fn in (install_githooks, install_cursor_rules):
        path = fn(dest)
        if path is not None:
            installed.append(path)
    installed.extend(install_ci_scaffold(dest))
    return installed


def std_file_sources() -> dict[str, Path]:
    """Map relative project paths to canonical sources (existing files only)."""
    out: dict[str, Path] = {}
    lic = license_src()
    if lic is not None:
        out["LICENSE"] = lic
    hook = githooks_pre_commit_src()
    if hook is not None:
        out[".githooks/pre-commit"] = hook
    for name in RULE_NAMES:
        rule = cursor_rule_src(name)
        if rule is not None:
            out[f".cursor/rules/{name}"] = rule
    ci = ci_scaffold_src()
    if ci is not None:
        for rel in (
            ".github/workflows/release-packages.yml",
            "scripts/ci/matrix.json",
            "scripts/ci/matrix-from-json.sh",
            "scripts/ci/build-deb.sh",
            "scripts/ci/build-rpm.sh",
            "scripts/ci/publish-private.sh",
            "scripts/ci/fetch-dep.sh",
            "scripts/ci/deps.conf.example",
        ):
            src = ci / rel
            if src.is_file():
                out[rel] = src
    return out
