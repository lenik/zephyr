# SPDX-License-Identifier: AGPL-3.0-or-later
"""RPM %files matching helpers for ``zfr lint``."""

from __future__ import annotations

import re
from pathlib import Path


def files_lines(body: str) -> list[str]:
    return [
        ln.strip()
        for ln in body.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def covers(body: list[str], expected: str) -> bool:
    """True when *expected* ``%files`` entry is already covered by *body*."""
    exp = expected.strip()
    if not exp:
        return True
    if exp in body:
        return True

    if exp.endswith("/*"):
        base = exp[:-2]
        if base in body or (base + "/") in body:
            return True
    elif exp.endswith("/"):
        if exp in body or (exp[:-1] + "/*") in body:
            return True
    else:
        if (exp + "/") in body or (exp + "/*") in body:
            return True

    if exp.startswith("%{_bindir}/") and (
        "%{_bindir}/*" in body or "%{_bindir}/" in body
    ):
        return True
    if "/bash-completion/completions/" in exp and any(
        "bash-completion/completions/*" in b for b in body
    ):
        return True
    # Spec globs like …/completions/zfr-* cover …/completions/zfr-create
    if "/bash-completion/completions/" in exp:
        base = exp.rsplit("/", 1)[-1]
        prefix = exp[: exp.rfind("/") + 1]
        for b in body:
            if not b.startswith(prefix):
                continue
            pat = b[len(prefix) :]
            if pat.endswith("*") and base.startswith(pat[:-1]):
                return True
            if pat.endswith("-*") and base.startswith(pat[:-1]):
                return True
    if exp.startswith("%{_mandir}/"):
        parts = exp.split("/")
        if len(parts) >= 3:
            section_glob = "/".join(parts[:3]) + "/*"
            if section_glob in body or "%{_mandir}/*" in body:
                return True
        if "/*/man" in exp and any("/*/man" in b for b in body):
            stem = parts[-1].rstrip("*")
            if any(stem in b for b in body):
                return True
    if exp.startswith("%{_sysconfdir}/") and any(
        b.startswith("%{_sysconfdir}") for b in body
    ):
        return True
    if exp.startswith("%{_includedir}/") and any(
        b.startswith("%{_includedir}") for b in body
    ):
        return True
    if "/perl5" in exp and any("perl5" in b for b in body):
        return True
    if "/shlib.d/" in exp and any("shlib.d" in b for b in body):
        return True
    if "/bash-alias/" in exp and any("bash-alias" in b for b in body):
        return True
    if "/setup/" in exp and any("/setup/" in b for b in body):
        return True
    if "/locale/" in exp and ".mo" in exp and any(
        "/locale/" in b and ".mo" in b for b in body
    ):
        return True
    if exp.startswith("%{_datadir}/doc/") or exp.startswith("%{_docdir}"):
        return any("/doc/" in b or "%{_docdir}" in b for b in body)
    return False


def has_meson_executable(root: Path) -> bool:
    from ..ize.rpm_files import _all_meson_texts

    return bool(re.search(r"\bexecutable\s*\(", _all_meson_texts(root)))
