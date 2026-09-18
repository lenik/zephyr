# SPDX-License-Identifier: AGPL-3.0-or-later
"""Detect packaging types and build packages via packager providers.

Public facade: detection, packager interface, and ``package_project``.
Implementations live in sibling modules (``deb``, ``npm``, ``make_target``, …).
"""

from __future__ import annotations

from .deb import DebPackager, package_deb
from .kinds import PackagingKind, detect_packaging_kinds, resolve_rpm_dir
from .make_target import MakeTargetPackager, package_make_target
from .npm import NpmPackager, package_npm_or_vsix
from .parallel import package_project
from .provider import Packager, PackagerContext
from .registry import packager_for
from .upload import upload_artifacts

__all__ = [
    "DebPackager",
    "MakeTargetPackager",
    "NpmPackager",
    "Packager",
    "PackagerContext",
    "PackagingKind",
    "detect_packaging_kinds",
    "package_deb",
    "package_make_target",
    "package_npm_or_vsix",
    "package_project",
    "packager_for",
    "resolve_rpm_dir",
    "upload_artifacts",
]
