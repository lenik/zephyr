# SPDX-License-Identifier: AGPL-3.0-or-later
"""Zephyr package *shape* scoring and monorepo layout (repodir / packagedir)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import (
    LANGS,
    RECOMMENDED_I18N_LINGUAS,
    _is_zfr_cli_package,
    _is_zfr_meta_repo,
)

# Predicate threshold for ``zfr shape -b`` (1 if score >= this).
SHAPE_BOOL_THRESHOLD = 50


@dataclass(frozen=True)
class ZephyrLayout:
    """Resolved monorepo layout for the current working context.

    *packagedir* is the language/app package tree (e.g. ``…/zephyr/bash``).
    *repodir* is the git / meta checkout root (e.g. ``…/zephyr``).
    They are equal for a standalone single-package repository.
    """

    packagedir: Path
    repodir: Path
    role: str  # meta | template | app | package

    @property
    def is_monorepo(self) -> bool:
        return self.packagedir.resolve() != self.repodir.resolve()


def _has_project_meson(d: Path) -> bool:
    meson = d / "meson.build"
    if not meson.is_file():
        return False
    head = meson.read_text(encoding="utf-8", errors="ignore")[:4000]
    return bool(re.search(r"^\s*project\s*\(", head, re.M))


def _is_package_candidate(d: Path) -> bool:
    """True when *d* looks like a project root ize/lint can operate on.

    Include Autotools/CMake/Maven trees that lack ``debian/`` yet — otherwise
    ``find_packagedir`` rejects pre-ize checkouts such as batch4/echo.
    """
    return (
        _has_project_meson(d)
        or (d / "debian" / "control").is_file()
        or (d / "configure.ac").is_file()
        or (d / "configure.in").is_file()
        or (d / "CMakeLists.txt").is_file()
        or (d / "pom.xml").is_file()
        or (d / "Makefile.am").is_file()
        or _is_zfr_meta_repo(d)
    )


def shape_score(root: Path | None = None) -> int:
    """Return 0–100 how completely *root* matches zephyr package style."""
    root = (root or Path.cwd()).resolve()
    if not root.is_dir():
        return 0

    score = 0

    # Core identity (40)
    if _has_project_meson(root):
        score += 15
        meson = (root / "meson.build").read_text(encoding="utf-8", errors="ignore")
        if "zfr version" in meson or "zephyr version" in meson:
            score += 5
        if 'license:' in meson.lower() and "AGPL" in meson:
            score += 5
    if (root / "debian" / "control").is_file():
        score += 10
    if (root / "debian" / "changelog").is_file():
        score += 5

    # Packaging / docs (35)
    if (root / "debian" / "copyright").is_file():
        score += 5
    rules = root / "debian" / "rules"
    if rules.is_file():
        txt = rules.read_text(encoding="utf-8", errors="ignore")
        if "--buildsystem=meson" in txt and "debian/build" in txt:
            score += 10
        elif rules.is_file():
            score += 3
    if (root / "LICENSE").is_file():
        score += 5
    if (root / "README.md").is_file() or (
        _is_zfr_cli_package(root) and (root.parent / "README.md").is_file()
    ):
        score += 5
    if (root / "README-zh.md").is_file() or (
        _is_zfr_cli_package(root) and (root.parent / "README-zh.md").is_file()
    ):
        score += 5
    docs = root / "docs"
    if docs.is_dir() and any(docs.glob("*.adoc")):
        score += 5

    # Optional polish (25)
    if any(root.glob("*.bash")) or any((root / "tools").glob("*.bash")):
        score += 5
    if (root / "VERSION").is_file():
        score += 5
    if (root / ".githooks" / "pre-commit").is_file():
        score += 5
    from .packaging import resolve_rpm_dir

    rpm = resolve_rpm_dir(root)
    if rpm.is_dir() and (any(rpm.glob("*.spec")) or (rpm / "Makefile").is_file()):
        score += 5
    po = root / "po"
    if po.is_dir() and (po / "LINGUAS").is_file():
        linguas = {
            ln.split("#", 1)[0].strip()
            for ln in (po / "LINGUAS").read_text(encoding="utf-8", errors="ignore").splitlines()
            if ln.split("#", 1)[0].strip()
        }
        covered = sum(1 for loc in RECOMMENDED_I18N_LINGUAS if loc in linguas)
        # up to 5 points proportional to recommended coverage
        score += min(5, (covered * 5) // max(1, len(RECOMMENDED_I18N_LINGUAS)))

    return max(0, min(100, score))


def shape_bool(root: Path | None = None, *, threshold: int = SHAPE_BOOL_THRESHOLD) -> bool:
    return shape_score(root) >= threshold


def find_repodir(start: Path | None = None) -> Path:
    """Git checkout root, else meta-repo root, else same as packagedir walk."""
    cur = (start or Path.cwd()).resolve()
    for d in [cur, *cur.parents]:
        if (d / ".git").exists():
            return d
    for d in [cur, *cur.parents]:
        if _is_zfr_meta_repo(d):
            return d
    # Fall back: outermost package candidate, else cwd
    last = cur
    for d in [cur, *cur.parents]:
        if _is_package_candidate(d):
            last = d
    return last


def find_packagedir(start: Path | None = None) -> Path:
    """Nearest package-shaped directory (prefer high shape over meta-repo root).

    In a monorepo ``repodir/packagedir``, this returns *packagedir* when cwd is
    inside it. Shape score distinguishes real packages from incidental parents.
    """
    cur = (start or Path.cwd()).resolve()
    repo = find_repodir(cur)
    best: Path | None = None
    best_score = -1

    for d in [cur, *cur.parents]:
        if not _is_package_candidate(d):
            if d == repo:
                break
            continue
        if _is_zfr_meta_repo(d):
            # Meta root is only chosen if nothing better was found below.
            if best is None:
                best = d
                best_score = shape_score(d)
            break
        sc = shape_score(d)
        # Prefer the closest directory that looks like a package (score > 0),
        # breaking ties by staying nearer to cwd (first wins if equal).
        if sc > best_score or (sc == best_score and best is None):
            best = d
            best_score = sc
        # Once we have a strong package match, stop climbing into the repo root.
        if sc >= SHAPE_BOOL_THRESHOLD and d != repo:
            return d
        if d == repo:
            break

    if best is not None:
        return best
    raise SystemExit(
        f"could not find a zephyr package directory at or above {cur}"
    )


def resolve_layout(start: Path | None = None) -> ZephyrLayout:
    """Resolve *packagedir* and *repodir* for *start* (default: cwd)."""
    cur = (start or Path.cwd()).resolve()
    packagedir = find_packagedir(cur)
    repodir = find_repodir(cur)
    # If packagedir is outside repo (odd), clamp repodir to packagedir.
    try:
        packagedir.resolve().relative_to(repodir.resolve())
    except ValueError:
        repodir = packagedir

    if _is_zfr_cli_package(packagedir):
        # The zephyr helper lives in zfr/ inside the meta-repo; it is not a
        # language template even though Source: zephyr and the parent is meta.
        role = "package"
    elif _is_zfr_meta_repo(packagedir):
        role = "meta"
    elif _is_zfr_meta_repo(repodir) and packagedir != repodir:
        role = "template"
    elif (packagedir / "debian" / "control").is_file() or _has_project_meson(packagedir):
        # Instantiated apps usually have rewritten names; templates keep zephyr.
        role = "package"
        control = packagedir / "debian" / "control"
        if control.is_file():
            txt = control.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"^Source:\s*zephyr\s*$", txt, re.M):
                if _is_zfr_meta_repo(repodir):
                    role = "template"
                else:
                    role = "app"
        meson = packagedir / "meson.build"
        if role == "package" and meson.is_file():
            mtxt = meson.read_text(encoding="utf-8", errors="ignore")[:800]
            if re.search(r"project\s*\(\s*['\"]zephyr['\"]", mtxt):
                role = "template" if _is_zfr_meta_repo(repodir) else "app"
    else:
        role = "package"

    return ZephyrLayout(packagedir=packagedir, repodir=repodir, role=role)


def cmd_shape(
    *,
    as_bool: bool = False,
    threshold: int = SHAPE_BOOL_THRESHOLD,
    workdir: Path | None = None,
    verbose: bool = False,
) -> int:
    """Print shape score (0–100) or 0/1 with ``--bool``. Exit 0 always on success."""
    start = (workdir or Path.cwd()).resolve()
    try:
        layout = resolve_layout(start)
        root = layout.packagedir
    except SystemExit:
        root = start
        layout = None

    score = shape_score(root)
    if as_bool:
        print(1 if score >= threshold else 0)
    else:
        print(score)
    if verbose and layout is not None:
        print(
            f"# packagedir={layout.packagedir}\n"
            f"# repodir={layout.repodir}\n"
            f"# role={layout.role}\n"
            f"# threshold={threshold}",
            file=__import__("sys").stderr,
        )
    return 0

import argparse
from .cli import register_command
from .i18n import _

NAME = "shape"
HELP = _("print zephyr package shape score 0-100 (packagedir vs repodir in monorepos)")
DESCRIPTION = _(
    "Score how completely the current directory matches zephyr "
    "package style (0-100). In monorepos, scores the packagedir."
)


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("-b", "--bool", action="store_true", dest="as_bool", help=_("print 1 if score >= threshold, else 0"))
    p.add_argument("-v", "--verbose", action="store_true", help=_("print packagedir/repodir/role on stderr"))
    p.add_argument("--threshold", type=int, default=SHAPE_BOOL_THRESHOLD, metavar="N", help=_("bool threshold 0-100 (default: %s)") % SHAPE_BOOL_THRESHOLD)


def run(args: argparse.Namespace) -> int:
    return cmd_shape(as_bool=args.as_bool, threshold=args.threshold, verbose=args.verbose)


def register(sub: argparse._SubParsersAction) -> None:
    register_command(sub, NAME, help=HELP, description=DESCRIPTION, add_arguments=add_arguments, run=run)
