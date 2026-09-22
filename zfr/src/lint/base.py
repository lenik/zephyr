# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rule module discovery and metadata for lint/ize."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


@dataclass
class RuleSpec:
    """Loaded rule module metadata."""

    id: str
    code: str
    module: ModuleType
    priority: float = 100.0
    dependencies: list[str] = field(default_factory=list)
    globs: list[str] = field(default_factory=lambda: ["/"])
    title: str = ""
    detail: str | None = None
    default_severity: str | None = None
    izeable: bool = False
    ize_targets: list[str] = field(default_factory=list)
    kind: str = "lint"  # lint | ize

    def matches(self, pathname: str, session: Any = None) -> bool:
        fn = getattr(self.module, "matches", None)
        if fn is None:
            return True
        try:
            return bool(fn(pathname, session))
        except TypeError:
            return bool(fn(pathname))

    def lint(self, files: list[Path], session: Any = None) -> list[Any]:
        fn = getattr(self.module, "lint", None)
        if fn is None:
            return []
        return list(fn(files, session) or [])

    def ize(self, files: list[Path], session: Any = None) -> Any:
        fn = getattr(self.module, "ize", None)
        if fn is None:
            from lint.editlist import EditList

            return EditList()
        return fn(files, session)


_ID_RE = re.compile(r"^(ZL|ZI)\d{4}$")


def _read_readme_title(rule_dir: Path) -> str:
    readme = rule_dir / "README.md"
    if not readme.is_file():
        return ""
    text = readme.read_text(encoding="utf-8", errors="replace")
    # YAML front matter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end]
            for line in fm.splitlines():
                if line.lower().startswith("title:"):
                    return line.split(":", 1)[1].strip().strip("\"'")
            text = text[end + 4 :]
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
        if s.startswith("## ") and not s.startswith("## Z"):
            return s[3:].strip()
    return ""


def load_rule_module(modpkg: str, rule_id: str) -> RuleSpec | None:
    """Import ``{modpkg}.{rule_id}.rule`` and build a RuleSpec.

    *modpkg* is the dotted package containing the rule dir, e.g.
    ``lint.rules`` or ``ize.rules``.
    """
    if not _ID_RE.match(rule_id):
        return None
    mod_name = f"{modpkg}.{rule_id}.rule"
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None
    rid = getattr(mod, "ID", rule_id)
    code = getattr(mod, "CODE", rid.lower())
    pkg_root = Path(mod.__file__).resolve().parent  # type: ignore[arg-type]
    title = getattr(mod, "TITLE", None) or _read_readme_title(pkg_root)
    return RuleSpec(
        id=rid,
        code=code,
        module=mod,
        priority=float(getattr(mod, "PRIORITY", 100.0)),
        dependencies=list(getattr(mod, "DEPENDENCIES", []) or []),
        globs=list(getattr(mod, "GLOBS", ["/"]) or ["/"]),
        title=title or code,
        detail=getattr(mod, "DETAIL", None),
        default_severity=getattr(mod, "DEFAULT_SEVERITY", None),
        izeable=bool(getattr(mod, "IZEABLE", False)),
        ize_targets=list(getattr(mod, "IZE_TARGETS", []) or []),
        kind="ize" if rid.startswith("ZI") else "lint",
    )


def discover_rules(
    package: str,
    *,
    prefix: str,
    subdir: str = "rules",
) -> list[RuleSpec]:
    """Discover ``{package}/{subdir}/{prefix}*/rule.py`` modules."""
    try:
        pkg = importlib.import_module(package)
    except ImportError:
        return []
    roots = [Path(p) for p in getattr(pkg, "__path__", [])]
    found: dict[str, RuleSpec] = {}
    for root in roots:
        search = root / subdir if subdir else root
        modpkg = f"{package}.{subdir}" if subdir else package
        if not search.is_dir():
            continue
        # Ensure namespace/package is importable
        try:
            importlib.import_module(modpkg)
        except ImportError:
            continue
        for child in sorted(search.iterdir()):
            if not child.is_dir():
                continue
            if not child.name.startswith(prefix):
                continue
            if not (child / "rule.py").is_file():
                continue
            spec = load_rule_module(modpkg, child.name)
            if spec is not None:
                found[spec.id] = spec
    return [found[k] for k in sorted(found)]


def specs_to_std_rules(specs: list[RuleSpec]):
    """Adapt RuleSpec list to StdRule registry for -L/-H compatibility."""
    from std.registry import RuleRegistry, StdRule

    rules = tuple(
        StdRule(
            s.id,
            s.code,
            s.title,
            s.default_severity,
            s.detail,
            izeable=s.izeable,
        )
        for s in specs
    )
    return RuleRegistry(rules)
