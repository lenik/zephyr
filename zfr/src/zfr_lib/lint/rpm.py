# SPDX-License-Identifier: AGPL-3.0-or-later
"""RPM packaging checks (aligned with ``zfr ize`` / ``zfr release -fIR``)."""

from __future__ import annotations

import re
from pathlib import Path

from .finding import Finding
from .util import *  # noqa: F403


def _files_lines(body: str) -> list[str]:
    return [
        ln.strip()
        for ln in body.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def _covers(body: list[str], expected: str) -> bool:
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


def _has_meson_executable(root: Path) -> bool:
    from ..ize.rpm_files import _all_meson_texts

    return bool(re.search(r"\bexecutable\s*\(", _all_meson_texts(root)))


def check_rpm(root: Path, lang: str) -> list[Finding]:
    out: list[Finding] = []
    specs = _specs(root)
    src, pkg, _ctl = _control(root)
    if not specs:
        out.append(
            Finding(
                "note",
                "rpm.missing",
                _(
                    "no rpm/*.spec (optional, but zephyr style includes RPM next to debian/)"
                ),
                "rpm/",
                # xgettext: no-python-format
                fix=_(
                    "Copy rpm/ from a language template; name the spec after the package "
                    "(rpm/<Source>.spec, not zephyr.spec) and keep a Makefile using "
                    "`zfr version`. Align Name/Summary/Requires/URL with debian/control. "
                    "Or run `zfr ize`."
                ),
            )
        )
        return out

    from ..ize.rpm_files import (
        files_section_body,
        meson_rpm_files,
        ships_gettext_mo,
        ships_locale_mans,
        _all_meson_texts,
    )

    name = (
        src.get("Source")
        or _meson_project_fields(root).get("name")
        or root.name
    )

    for spec in specs:
        rel = _rel(root, spec)
        text = _read(spec)
        makefile = root / "rpm" / "Makefile"
        mk = _read(makefile)
        files_body = files_section_body(text)
        lines = _files_lines(files_body)

        if makefile.is_file():
            from ..packaging import makefile_uses_local_rpmbuild

            if makefile_uses_local_rpmbuild(mk):
                out.append(
                    Finding(
                        "error",
                        "rpm.topdir.local",
                        # xgettext: no-python-format
                        _(
                            "rpm/Makefile uses project-local <project>/rpmbuild; "
                            "zephyr style uses %_topdir ($HOME/rpmbuild, "
                            "override via ~/.rpmmacros)"
                        ),
                        "rpm/Makefile",
                        line=_line_of(mk, "TOPDIR"),
                        # xgettext: no-python-format
                        fix=_(
                            "TOPDIR ?= $(shell rpm --eval '%{_topdir}' 2>/dev/null)\n"
                            "ifeq ($(strip $(TOPDIR)),)\n"
                            "TOPDIR := $(HOME)/rpmbuild\n"
                            "endif\n"
                            "And make clean remove only this package's artifacts "
                            "(not rm -rf $(TOPDIR)). Or run `zfr ize`."
                        ),
                    )
                )
            else:
                out.append(
                    Finding(
                        "ok",
                        "rpm.topdir",
                        # xgettext: no-python-format
                        _("rpm/Makefile TOPDIR uses %_topdir / $HOME/rpmbuild"),
                        "rpm/Makefile",
                    )
                )
            if re.search(r"(?m)^clean:\n\trm -rf \$\(TOPDIR\)\s*$", mk):
                out.append(
                    Finding(
                        "error",
                        "rpm.topdir.clean",
                        _(
                            "rpm/Makefile `clean` does rm -rf $(TOPDIR); "
                            "unsafe when TOPDIR is $HOME/rpmbuild"
                        ),
                        "rpm/Makefile",
                        line=_line_of(mk, "clean:"),
                        fix=_(
                            "Remove only this package's SPECS/SOURCES/RPMS/SRPMS/"
                            "BUILD/BUILDROOT entries under $(TOPDIR). Or run `zfr ize`."
                        ),
                    )
                )
            local_tree = root / "rpmbuild"
            if local_tree.is_dir():
                out.append(
                    Finding(
                        "warn",
                        "rpm.topdir.leftover",
                        # xgettext: no-python-format
                        _(
                            "project-local rpmbuild/ directory present; "
                            "builds should use %_topdir ($HOME/rpmbuild)"
                        ),
                        "rpmbuild/",
                        fix=_("Remove rpmbuild/ after migrating; safe to delete."),
                    )
                )

        # ---- Version / license / metadata ----
        if "%{version}" in text or "%{!?version" in text or "%{?version" in text:
            out.append(
                Finding(
                    "ok",
                    "rpm.dynamic_version",
                    # xgettext: no-python-format
                    _("spec Version is dynamic %{version}"),
                    rel,
                )
            )
        elif re.search(r"^Version:\s*[0-9]", text, re.M):
            out.append(
                Finding(
                    "error",
                    "rpm.dynamic_version",
                    _("spec Version is hardcoded; zephyr style injects `zfr version`"),
                    rel,
                    line=_line_of(text, "Version:"),
                    # xgettext: no-python-format
                    fix=_(
                        "Use Version: %{version} with %{!?version:%global version 0.0.0} "
                        "and freeze via rpm/Makefile (`zfr version` / `zfr version -r`)."
                    ),
                )
            )

        if _AGPL in text:
            out.append(
                Finding("ok", "rpm.license", _("License {}").format(_AGPL), rel)
            )
        else:
            out.append(
                Finding(
                    "warn",
                    "rpm.license",
                    _("spec License is not AGPL-3.0-or-later"),
                    rel,
                    line=_line_of(text, "License:"),
                    fix=_("License:        {}").format(_AGPL),
                )
            )

        url = re.search(r"^URL:\s*(\S+)", text, re.M)
        homepage = src.get("Homepage", "")
        if url and homepage and url.group(1).rstrip("/") != homepage.rstrip("/"):
            out.append(
                Finding(
                    "warn",
                    "rpm.URL",
                    _("spec URL={!r} != debian Homepage={!r}").format(
                        url.group(1), homepage
                    ),
                    rel,
                    fix=_("Set URL: to the same Homepage as debian/control."),
                )
            )

        summary = re.search(r"^Summary:\s*(.+)$", text, re.M)
        desc = pkg.get("Description", "")
        deb_summary = desc.split("\n", 1)[0].strip() if desc else ""
        if summary and deb_summary and summary.group(1).strip() != deb_summary:
            out.append(
                Finding(
                    "warn",
                    "rpm.Summary",
                    _("spec Summary does not match debian Description first line"),
                    rel,
                    line=_line_of(text, "Summary:"),
                    fix=_("Summary:        {}").format(deb_summary),
                )
            )

        if "meson" in text.lower() and "%configure" not in text:
            out.append(
                Finding("ok", "rpm.build", _("spec uses Meson (not autotools)"), rel)
            )
        elif "%configure" in text or "autoreconf" in text:
            out.append(
                Finding(
                    "error",
                    "rpm.build",
                    _("spec still uses autotools; zephyr packages build with Meson"),
                    rel,
                    # xgettext: no-python-format
                    fix=_(
                        "%build: meson setup build --prefix=%{_prefix} ... && "
                        "meson compile -C build\n"
                        "%install: meson install -C build --destdir=%{buildroot}"
                    ),
                )
            )

        if makefile.is_file():
            if "zfr version" in mk:
                out.append(
                    Finding(
                        "ok",
                        "rpm.makefile.version",
                        _("Makefile uses `zfr version`"),
                        "rpm/Makefile",
                    )
                )
            else:
                out.append(
                    Finding(
                        "warn",
                        "rpm.makefile.version",
                        _("rpm/Makefile does not call `zfr version`"),
                        "rpm/Makefile",
                        # xgettext: no-python-format
                        fix=_(
                            "VERSION := $(shell cd \"$(SRCDIR)\" && zfr version)\n"
                            "RPM_VERSION := $(shell cd \"$(SRCDIR)\" && zfr version -r)"
                        ),
                    )
                )
        else:
            out.append(
                Finding(
                    "note",
                    "rpm.makefile",
                    _("no rpm/Makefile convenience targets"),
                    "rpm/Makefile",
                    fix=_("Copy bash/rpm/Makefile (srpm/rpm via zfr version)."),
                )
            )

        if lang == "bash" and "bash-shlib" not in text:
            out.append(
                Finding(
                    "error",
                    "rpm.Requires.bash-shlib",
                    _("bash spec Requires missing bash-shlib"),
                    rel,
                    fix=_("Requires:       bash-shlib  (same as debian Depends)"),
                )
            )

        # ---- Debian substvars leaked into RPM Requires ----
        for m in re.finditer(
            r"(?mi)^(Requires|BuildRequires|Recommends|Suggests):\s*(.*)$", text
        ):
            if "${" in m.group(2):
                out.append(
                    Finding(
                        "error",
                        "rpm.substvar",
                        _(
                            "{} still contains Debian ${{…}} substvars "
                            "(rpmbuild treats them as literal deps)"
                        ).format(m.group(1)),
                        rel,
                        line=_line_of(text, m.group(0)[:40]),
                        fix=_(
                            "Strip ${misc:Depends} / ${shlibs:Depends} etc. "
                            "(or run `zfr ize`)."
                        ),
                    )
                )
                break

        # ---- noarch vs Meson executable() ----
        has_elf = _has_meson_executable(root)
        if has_elf and re.search(r"(?m)^BuildArch:\s*noarch\b", text):
            out.append(
                Finding(
                    "error",
                    "rpm.noarch.elf",
                    _(
                        "BuildArch: noarch but Meson has executable(); "
                        "rpmbuild rejects arch-dependent binaries in a noarch package"
                    ),
                    rel,
                    line=_line_of(text, "BuildArch:"),
                    # xgettext: no-python-format
                    fix=_(
                        "Remove BuildArch: noarch (and %global debug_package %{nil} "
                        "if present). Or run `zfr ize`."
                    ),
                )
            )
        elif has_elf and re.search(
            r"(?m)^%global\s+debug_package\s+%\{nil\}", text
        ):
            out.append(
                Finding(
                    "warn",
                    "rpm.debug_package.elf",
                    # xgettext: no-python-format
                    _(
                        "%global debug_package %{nil} on a package with Meson "
                        "executable() — debuginfo would be useful"
                    ),
                    rel,
                    # xgettext: no-python-format
                    fix=_("Drop %global debug_package %{nil} for ELF packages."),
                )
            )

        # ---- Template puff leftovers ----
        if TEMPLATE_PUFF in files_body or "some_puff1" in files_body:
            out.append(
                Finding(
                    "error",
                    "rpm.files.puff",
                    _("RPM %files still lists template puff {}").format(
                        TEMPLATE_PUFF
                    ),
                    rel,
                    line=_line_of(text, "%files"),
                    fix=_(
                        "Replace {} with real command names (or run `zfr ize`)."
                    ).format(TEMPLATE_PUFF),
                )
            )

        # ---- gettext / locale mans ----
        if ships_gettext_mo(root):
            if "/locale/" in files_body and ".mo" in files_body:
                out.append(
                    Finding(
                        "ok",
                        "rpm.files.mo",
                        # xgettext: no-python-format
                        _("%files covers gettext .mo catalogs Meson installs"),
                        rel,
                    )
                )
            else:
                out.append(
                    Finding(
                        "error",
                        "rpm.files.mo",
                        # xgettext: no-python-format
                        _(
                            "%files omits gettext .mo; rpmbuild will reject unpackaged "
                            "locale/*/LC_MESSAGES/*.mo after meson install"
                        ),
                        rel,
                        line=_line_of(text, "%files"),
                        # xgettext: no-python-format
                        fix=_(
                            "%{_datadir}/locale/*/LC_MESSAGES/<name>.mo  "
                            "(Meson i18n.gettext / po/). Or run `zfr ize`."
                        ),
                    )
                )

        if ships_locale_mans(root):
            if "%{_mandir}/*/man" in files_body or re.search(
                r"%\{_mandir\}/\*/man[0-9]", files_body
            ):
                out.append(
                    Finding(
                        "ok",
                        "rpm.files.locale_man",
                        # xgettext: no-python-format
                        _("%files covers locale man pages Meson installs"),
                        rel,
                    )
                )
            else:
                out.append(
                    Finding(
                        "error",
                        "rpm.files.locale_man",
                        # xgettext: no-python-format
                        _(
                            "%files omits locale mans; rpmbuild will reject unpackaged "
                            "$mandir/<locale>/manN pages after meson install"
                        ),
                        rel,
                        line=_line_of(text, "%files"),
                        # xgettext: no-python-format
                        fix=_(
                            "%{_mandir}/*/man1/<cmd>.1*  "
                            "(docs/<lang>/*.adoc). Or run `zfr ize`."
                        ),
                    )
                )

        # ---- setup/ scripts ----
        meson_blob = _all_meson_texts(root)
        needs_setup = (
            (root / "postinst.in").is_file()
            or (root / "prerm.in").is_file()
            or bool(
                re.search(r"['\"]setup['\"]\s*/\s*meson\.project_name", meson_blob)
            )
        )
        if needs_setup:
            if any("/setup/" in ln for ln in lines):
                out.append(
                    Finding(
                        "ok",
                        "rpm.files.setup",
                        # xgettext: no-python-format
                        _("%files covers datadir/setup scripts Meson installs"),
                        rel,
                    )
                )
            else:
                out.append(
                    Finding(
                        "error",
                        "rpm.files.setup",
                        # xgettext: no-python-format
                        _(
                            "%files omits datadir/setup/*; rpmbuild will reject unpackaged "
                            "postinst/prerm after meson install"
                        ),
                        rel,
                        line=_line_of(text, "%files"),
                        # xgettext: no-python-format
                        fix=_("%{_datadir}/setup/%{name}/  (or run `zfr ize`)."),
                    )
                )

        # ---- Meson-derived %files coverage ----
        expected = meson_rpm_files(root, name)
        meaningful = any(
            x.startswith("%{_bindir}/")
            or x.startswith("%{_mandir}/")
            or "/bash-completion/" in x
            or "/shlib.d/" in x
            or x.startswith("%{_sysconfdir}/")
            or x.startswith("%{_includedir}/")
            or "/perl5" in x
            or "/setup/" in x
            or x.startswith("%{_datadir}/%{name}")
            for x in expected
        )
        if expected and meaningful:
            missing = [
                e
                for e in expected
                if not e.startswith("%{_datadir}/doc/")
                and not e.startswith("%{_docdir}")
                and not _covers(lines, e)
            ]
            if missing:
                preview = ", ".join(missing[:8])
                more = f" (+{len(missing) - 8} more)" if len(missing) > 8 else ""
                out.append(
                    Finding(
                        "error",
                        "rpm.files.meson",
                        # xgettext: no-python-format
                        _(
                            "%files is missing paths Meson installs: {preview}{more} "
                            "(rpmbuild will fail with unpackaged or File not found)"
                        ).format(preview=preview, more=more),
                        rel,
                        line=_line_of(text, "%files"),
                        # xgettext: no-python-format
                        fix=_(
                            "Rewrite %files from Meson install rules "
                            "(bindir, completions, manN, pkgdata, perl5, "
                            "includedir, sysconfdir, shlib.d, setup/). "
                            "Or run `zfr ize`."
                        ),
                    )
                )
            else:
                out.append(
                    Finding(
                        "ok",
                        "rpm.files.meson",
                        # xgettext: no-python-format
                        _(
                            "%files covers Meson install set ({} entries)"
                        ).format(len(expected)),
                        rel,
                    )
                )

            # Spurious pkgdata (Directory not found).
            for ln in lines:
                if re.fullmatch(r"%\{_datadir\}/%\{name\}/?\*?", ln):
                    if not any(
                        e.startswith("%{_datadir}/%{name}") for e in expected
                    ):
                        out.append(
                            Finding(
                                "error",
                                "rpm.files.spurious_pkgdata",
                                # xgettext: no-python-format
                                _(
                                    "%files lists %{_datadir}/%{name}/ but Meson does "
                                    "not install package data there (Directory not found)"
                                ),
                                rel,
                                line=_line_of(text, ln[:40]),
                                fix=_(
                                    "Remove the empty pkgdata line "
                                    "(Java template leftover). Or run `zfr ize`."
                                ),
                            )
                        )
                    break

            # Completion basename mismatch (coolutils vs coolutils.sh).
            for ln in lines:
                m = re.search(
                    r"%\{_datadir\}/bash-completion/completions/([^\s*]+)\s*$",
                    ln,
                )
                if not m:
                    continue
                listed = m.group(1)
                for e in expected:
                    if "/bash-completion/completions/" not in e:
                        continue
                    want = e.rsplit("/", 1)[-1]
                    if want == listed + ".sh":
                        out.append(
                            Finding(
                                "error",
                                "rpm.files.completion_basename",
                                _(
                                    "%files lists completion {listed!r} but Meson "
                                    "installs {want!r} (File not found)"
                                ).format(listed=listed, want=want),
                                rel,
                                line=_line_of(text, ln[:50]),
                                fix=_(
                                    "Use the installed basename ({}). Or run `zfr ize`."
                                ).format(want),
                            )
                        )

    return out
