# SPDX-License-Identifier: AGPL-3.0-or-later
"""Map :class:`~.kinds.PackagingKind` → :class:`~.provider.Packager` impl."""

from __future__ import annotations

from .deb import DebPackager
from .kinds import PackagingKind
from .make_target import MakeTargetPackager
from .npm import NpmPackager
from .provider import Packager


def packager_for(kind: PackagingKind) -> Packager:
    """Return the implementation that builds *kind*."""
    if kind.name == "deb":
        return DebPackager()
    if kind.name in {"npm", "vsix"}:
        return NpmPackager(kind.name)
    return MakeTargetPackager(kind.name, kind.path)
