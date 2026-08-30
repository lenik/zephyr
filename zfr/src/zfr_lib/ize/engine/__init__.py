# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ize engine: bring a tree up to current zephyr style."""
from __future__ import annotations

from .. import man as _man
from .. import spec as _spec
from ..debian import (
    ensure_debian_docs,
    ensure_debian_rules_meson,
    ensure_rpm_bash_shlib,
    ensure_rpm_noarch_nodebug,
    strip_rpm_substvars,
    patch_debian_control,
    strip_readme_banner,
)
from ..rpm_files import _all_meson_texts, sync_rpm_files
from ..util import *  # noqa: F403
from ...i18n import _

convert_man_file = _man.convert_man_file
groff_to_adoc = _man.groff_to_adoc
_man_target = _man._man_target
strip_install_man_paths = _man.strip_install_man_paths
stub_man_adoc = _man.stub_man_adoc
discover_man_stems = _man.discover_man_stems
strip_help2man_blocks = _man.strip_help2man_blocks
render_spec = _spec.render_spec
# Names used by Ize methods copied from ize.py:
convert_man_file = convert_man_file
groff_to_adoc = groff_to_adoc
_man_target = _man_target
strip_install_man_paths = strip_install_man_paths
render_spec = render_spec

class Ize:
    def __init__(
        self,
        root: Path,
        *,
        lang: str,
        dry_run: bool = False,
        do_man: bool = True,
        do_subst: bool = True,
        do_mesonize: bool = True,
        do_commit: bool = False,
        author: str | None = None,
        verbose: bool = False,
        color: str = "auto",
        uncheck: list[str] | None = None,
    ) -> None:
        from ...std import is_suppressed, ize_rule_id, parse_uncheck

        self.root = root
        self.lang = lang
        self.dry_run = dry_run
        self.do_man = do_man
        self.do_subst = do_subst
        self.do_mesonize = do_mesonize
        self.do_commit = do_commit
        self.author = author
        self.verbose = verbose
        self.csr = Csr(color)
        self.changes: list[Change] = []
        self._mesonized = False
        self._current_rule = ""
        self._suppressed = parse_uncheck(uncheck)
        self._is_suppressed = lambda code: is_suppressed(
            rule_id=ize_rule_id(code),
            code=code,
            suppressed=self._suppressed,
        )
        meson = _meson_project_fields(root)
        src, _, _ = _control(root)
        self.name = src.get("Source") or meson.get("name") or root.name
        self.pairs = instantiation_pairs(self.name)

    def note(self, kind: str, path: str, detail: str, *, rule: str | None = None) -> None:
        self.changes.append(
            Change(kind, path, detail, rule=rule or self._current_rule)
        )

    def _step(self, rule: str, fn) -> None:
        if self._is_suppressed(rule):
            if self.verbose:
                self.note("skip", rule, _("suppressed via -u/--uncheck"), rule=rule)
            return
        prev = self._current_rule
        self._current_rule = rule
        try:
            fn()
        finally:
            self._current_rule = prev

    def write_text(self, path: Path, text: str, detail: str, *, kind: str = "add") -> None:
        rel = _rel(self.root, path)
        existed = path.is_file()
        if existed:
            kind = "update"
        self.note(kind, rel, detail)
        if self.dry_run:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def copy_file(self, src: Path, dest: Path, detail: str) -> None:
        rel = _rel(self.root, dest)
        self.note("add", rel, detail)
        if self.dry_run:
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        copy_renamed_file(src, dest, self.pairs)
        if dest.name in {"rules", "pre-commit"}:
            mode = dest.stat().st_mode
            dest.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def run(self) -> int:
        self._step("ize.mesonize", self.mesonize)
        self._step("ize.scaffold", self.add_missing_files)
        self._step("ize.debian.control", self.patch_debian_control)
        self._step("ize.debian.rules", self.ensure_debian_rules)
        self._step("ize.debian.docs", self.fix_debian_docs)
        self._step("ize.changelog", self.ensure_changelog_version)
        self._step("ize.hooks", self.ensure_hooks)
        self._step("ize.meson.patch", self.patch_meson)
        if self.do_man:
            self._step("ize.man.convert", self.convert_manpages)
            self._step("ize.man.stub", self.ensure_man_stubs)
            self._step("ize.meson.man", self.patch_meson_man_targets)
        self._step("ize.completion", self.ensure_completion)
        self._step("ize.meson.patch", self.patch_meson)
        self._step("ize.rpm", self.ensure_rpm)
        if self.do_subst:
            self._step("ize.subst", self.subst_versions)
        self._step("ize.i18n.derive", self.derive_i18n_locales)
        self.report()
        if self.do_commit:
            self._step("ize.commit", self.commit_changes)
        return 0

    def mesonize(self) -> None:
        """Convert Autotools/CMake to Meson via 2meson (default on)."""
        from ..mesonize import find_2meson, has_foreign_build, run_2meson

        if not self.do_mesonize:
            if self.verbose:
                self.note("skip", "2meson", "--no-mesonize")
            return
        if not has_foreign_build(self.root):
            if self.verbose:
                self.note("skip", "2meson", "no Autotools/CMake sources")
            return
        exe = find_2meson()
        if exe is None:
            raise SystemExit(
                "zfr ize: Autotools/CMake detected but 2meson not found in PATH "
                "(install 2meson or set ZFR_2MESON)"
            )
        # Force overwrite when meson.build already exists alongside configure.ac
        # so a prior partial conversion can be refreshed.
        force = True
        detail = f"via {exe}"
        if self.dry_run:
            self.note("convert", "meson.build", f"would run 2meson {detail}")
            code, out = run_2meson(
                self.root, dry_run=True, force=force, verbose=self.verbose
            )
            if code != 0:
                raise SystemExit(f"zfr ize: 2meson dry-run failed (exit {code}):\n{out}")
            self._mesonized = True
            return
        code, out = run_2meson(
            self.root, dry_run=False, force=force, verbose=self.verbose
        )
        if code != 0:
            raise SystemExit(f"zfr ize: 2meson failed (exit {code}):\n{out}")
        self._mesonized = True
        self.note("convert", "meson.build", f"2meson {detail}")
        if self.verbose and out.strip():
            for line in out.strip().splitlines()[:20]:
                self.note("note", "2meson", line.strip())
    def add_missing_files(self) -> None:
        try:
            tmpl = template_dir(self.lang)
        except SystemExit:
            tmpl = None
        if tmpl is not None and tmpl.resolve() == self.root.resolve():
            tmpl_copy = tmpl
        else:
            tmpl_copy = tmpl
        meson_dest = self.root / "meson.build"
        if (
            not meson_dest.is_file()
            and not self._mesonized
            and tmpl_copy is not None
        ):
            src = tmpl_copy / "meson.build"
            if src.is_file():
                self.copy_file(src, meson_dest, "meson.build from language template")
        if tmpl_copy is None:
            return
        for rel in SCAFFOLD:
            dest = self.root / rel
            src = tmpl_copy / rel
            if dest.exists():
                if self.verbose:
                    self.note("skip", rel, "already present")
                continue
            if not src.is_file():
                continue
            if rel in ("README.md", "README-zh.md"):
                raw = src.read_text(encoding="utf-8", errors="ignore")
                text = strip_readme_banner(raw, self.name)
                # Also swap template puff placeholders.
                text = text.replace(TEMPLATE_PUFF, self.name)
                text = text.replace("some_puff1", self.name)
                self.write_text(dest, text, f"from {self.lang} template (banner stripped)")
            else:
                self.copy_file(src, dest, f"from {self.lang} template")

    def patch_debian_control(self) -> None:
        path = self.root / "debian" / "control"
        if not path.is_file():
            return
        text = path.read_text(encoding="utf-8")
        new, notes = patch_debian_control(text, lang=self.lang)
        if new != text:
            self.write_text(path, new, ", ".join(notes) or "debian/control lint alignment")

        compat = self.root / "debian" / "compat"
        if compat.is_file():
            # debhelper-compat in control supersedes debian/compat; drop stale levels.
            try:
                compat.unlink()
                self.note("convert", "debian/compat", "removed (use debhelper-compat in control)")
            except OSError:
                pass

    def ensure_debian_rules(self) -> None:
        path = self.root / "debian" / "rules"
        if not path.is_file():
            return
        text = path.read_text(encoding="utf-8", errors="ignore")
        new, notes = ensure_debian_rules_meson(text)
        if new != text:
            # Keep executable bit.
            mode = path.stat().st_mode
            self.write_text(path, new, ", ".join(notes) or "debian/rules")
            path.chmod(mode)

    def fix_debian_docs(self) -> None:
        notes = ensure_debian_docs(self.root)
        if notes:
            self.note("update", "debian/docs", ", ".join(notes))
    def ensure_man_stubs(self) -> None:
        """Create docs/*.adoc stubs when Autotools mans were help2man-only."""
        docs = self.root / "docs"
        existing = list(docs.glob("*.adoc")) if docs.is_dir() else []
        stems = discover_man_stems(self.root, self.name)
        # Only create stubs for stems that lack adoc.
        missing = [(s, sec) for s, sec in stems if not (docs / f"{s}.adoc").is_file()]
        if not missing and existing:
            # Still strip help2man if we already have adoc.
            meson = self.root / "meson.build"
            if meson.is_file():
                text = meson.read_text(encoding="utf-8")
                cleaned = strip_help2man_blocks(text)
                if cleaned != text:
                    self.write_text(meson, cleaned, "remove help2man blocks (AsciiDoc mans)")
            return
        if not missing:
            missing = [(self.name, "1")]
        summary = ""
        control = self.root / "debian" / "control"
        if control.is_file():
            m = re.search(
                r"^Description:\s*(.+)$",
                control.read_text(encoding="utf-8", errors="ignore"),
                re.M,
            )
            if m:
                summary = m.group(1).strip()
        for stem, section in missing:
            dest = docs / f"{stem}.adoc"
            body = stub_man_adoc(stem, section, summary=summary or f"{stem} utility")
            self.write_text(dest, body, "AsciiDoc man stub for lint/layout.docs")
        meson = self.root / "meson.build"
        if meson.is_file():
            text = meson.read_text(encoding="utf-8")
            cleaned = strip_help2man_blocks(text)
            if cleaned != text:
                self.write_text(meson, cleaned, "remove help2man blocks (AsciiDoc mans)")

    def ensure_completion(self) -> None:
        """Ensure a bash-completion stub exists for each command puff."""
        if self.lang != "bash":
            return
        puffs = _puff_names(self.root) or [self.name]
        for puff in puffs:
            dest = self.root / f"{puff}.bash"
            if dest.is_file():
                continue
            alt = self.root / "completions" / f"{puff}.bash"
            if alt.is_file():
                continue
            body = (
                f"# bash completion for {puff} (stub; extend as needed)\n"
                f"complete -F _longopt {puff} 2>/dev/null || true\n"
            )
            self.write_text(dest, body, f"bash-completion stub {puff}")

    def ensure_changelog_version(self) -> None:
        changelog = self.root / "debian" / "changelog"
        if not changelog.is_file():
            if self.dry_run:
                self.note("add", "debian/changelog", "initial changelog")
            else:
                author, email = _maintainer(self.root)
                ver = version_file_version(self.root) or DEFAULT_INIT_VERSION
                _write_debian_changelog(
                    self.root,
                    package=self.name,
                    version=ver,
                    distribution=DEFAULT_DISTRIBUTION,
                    author=author,
                    email=email,
                )
                self.note("add", "debian/changelog", f"{self.name} ({ver})")
        ver = changelog_version(self.root)
        version_path = self.root / "VERSION"
        if ver and (not version_path.is_file() or version_file_version(self.root) != ver):
            self.write_text(version_path, ver + "\n", "snapshot of debian/changelog")

    def ensure_hooks(self) -> None:
        hook = self.root / ".githooks" / "pre-commit"
        if hook.is_file():
            if self.verbose:
                self.note("skip", ".githooks/pre-commit", "already present")
            return
        if self.dry_run:
            self.note("add", ".githooks/pre-commit", "VERSION sync hook")
            return
        _install_githooks(self.root)
        if hook.is_file():
            self.note("add", ".githooks/pre-commit", "VERSION sync hook")
            git = shutil.which("git")
            if git and (self.root / ".git").exists():
                subprocess.run(
                    [git, "config", "core.hooksPath", ".githooks"],
                    cwd=self.root,
                    check=False,
                )


    def patch_meson(self) -> None:
        from .meson import patch_meson_build
        patch_meson_build(self)

    def convert_manpages(self) -> None:
        from .meson import convert_manpages as _convert_manpages
        _convert_manpages(self)

    def patch_meson_man_targets(self) -> None:
        from .meson import patch_meson_man_targets as _patch
        _patch(self)

    def ensure_rpm(self) -> None:
        from .rpm import ensure_rpm_spec
        ensure_rpm_spec(self)

    def subst_versions(self) -> None:
        from .subst import subst_versions as _subst_versions
        _subst_versions(self)

    def _ensure_config_h(self) -> None:
        from .subst import ensure_config_h
        ensure_config_h(self)

    def _ensure_ize_scripts(self, ins: list[Path]) -> None:
        from .subst import ensure_ize_scripts
        ensure_ize_scripts(self, ins)

    def derive_i18n_locales(self) -> None:
        from ...i18n.builder import derive_locales

        if self.dry_run:
            written = derive_locales(self.root, dry_run=True)
            for rel in written:
                self.note("would-derive", rel, "child locale from parent")
            return
        for rel in derive_locales(self.root):
            self.note("derive", rel, "child locale from parent")


    def report(self) -> None:
        csr = self.csr
        adds = sum(1 for c in self.changes if c.kind == "add")
        updates = sum(1 for c in self.changes if c.kind == "update")
        converts = sum(1 for c in self.changes if c.kind == "convert")
        skips = sum(1 for c in self.changes if c.kind == "skip")
        head = csr.wrap("zfr ize", csr.bold)
        dry = "  dry-run" if self.dry_run else ""
        print(
            f"{head}: {self.root}  name={self.name}  lang={self.lang}{dry}",
            flush=True,
        )
        kind_color = {
            "add": csr.green,
            "update": csr.yellow,
            "convert": csr.cyan,
            "skip": csr.dim,
            "note": csr.dim,
        }
        shown = [c for c in self.changes if c.kind not in {"skip", "note"} or self.verbose]
        for c in shown:
            tag = csr.wrap(f"{c.kind:7}", csr.bold, kind_color.get(c.kind, ""))
            rid = ""
            if c.rule:
                from ...std import ize_rule_id

                rid = csr.wrap(ize_rule_id(c.rule), csr.bold, csr.magenta) + " "
            path = csr.wrap(c.path, csr.bold, csr.blue)
            print(f"  {tag} {rid}{path}  {c.detail}", flush=True)
        print(
            f"done: {adds} added, {updates} updated, {converts} converted"
            + (f", {skips} skipped" if self.verbose else ""),
            flush=True,
        )
        if not self.dry_run:
            print("re-run `zfr lint` to check remaining style gaps.", flush=True)


    def commit_message(self) -> str:
        from .commit import commit_message as _commit_message
        return _commit_message(self)

    def _changelog_bullets(self) -> list[str]:
        from .commit import changelog_bullets
        return changelog_bullets(self)

    def bump_for_commit(self) -> str | None:
        from .commit import bump_for_commit as _bump
        return _bump(self)

    def commit_changes(self) -> None:
        from .commit import commit_changes as _commit_changes
        _commit_changes(self)

