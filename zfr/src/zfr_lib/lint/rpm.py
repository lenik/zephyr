# SPDX-License-Identifier: AGPL-3.0-or-later
"""RPM packaging checks (aligned with ``zfr ize`` / ``zfr release -fIR``)."""

from __future__ import annotations

import re
from pathlib import Path

from .finding import Finding
from .rpm_util import covers, files_lines, has_meson_executable
from .util import *  # noqa: F403


def check_rpm(root: Path, lang: str) -> list[Finding]:
    from ..packaging import resolve_rpm_dir

    out: list[Finding] = []
    specs = _specs(root)
    src, pkg, _ctl = _control(root)
    if not specs:
        out.append(
            Finding(
                "note",
                "rpm.missing",
                _(
                    "no packaging/rpm/*.spec (optional, but zephyr style includes RPM next to debian/)"
                ),
                "packaging/rpm/",
                # xgettext: no-python-format
                fix=_(
                    "Copy packaging/rpm/ from a language template; name the spec after the package "
                    "(packaging/rpm/<Source>.spec, not zephyr.spec) and keep a Makefile using "
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
        makefile = resolve_rpm_dir(root) / "Makefile"
        mk = _read(makefile)
        files_body = files_section_body(text)
        lines = files_lines(files_body)

        if makefile.is_file():
            from ..packaging import makefile_uses_local_rpmbuild

            if makefile_uses_local_rpmbuild(mk):
                out.append(
                    Finding(
                        "error",
                        "rpm.topdir.local",
                        # xgettext: no-python-format
                        _(
                            "packaging/rpm/Makefile uses project-local <project>/rpmbuild; "
                            "zephyr style uses %_topdir ($HOME/rpmbuild, "
                            "override via ~/.rpmmacros)"
                        ),
                        "packaging/rpm/Makefile",
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
                        _("packaging/rpm/Makefile TOPDIR uses %_topdir / $HOME/rpmbuild"),
                        "packaging/rpm/Makefile",
                    )
                )
            if re.search(r"(?m)^clean:\n\trm -rf \$\(TOPDIR\)\s*$", mk):
                out.append(
                    Finding(
                        "error",
                        "rpm.topdir.clean",
                        _(
                            "packaging/rpm/Makefile `clean` does rm -rf $(TOPDIR); "
                            "unsafe when TOPDIR is $HOME/rpmbuild"
                        ),
                        "packaging/rpm/Makefile",
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
                        "and freeze via packaging/rpm/Makefile (`zfr version` / `zfr version -r`)."
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
                        "packaging/rpm/Makefile",
                    )
                )
            else:
                out.append(
                    Finding(
                        "warn",
                        "rpm.makefile.version",
                        _("packaging/rpm/Makefile does not call `zfr version`"),
                        "packaging/rpm/Makefile",
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
                    _("no packaging/rpm/Makefile convenience targets"),
                    "packaging/rpm/Makefile",
                    fix=_("Copy bash/packaging/rpm/Makefile (srpm/rpm via zfr version)."),
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
        has_elf = has_meson_executable(root)
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
        elif (
            not has_elf
            and lang in {"bash", "python", "perl", "java", "ruby", "typescript"}
            and not re.search(r"(?m)^BuildArch:\s*noarch\b", text)
        ):
            out.append(
                Finding(
                    "error",
                    "rpm.noarch.script",
                    _(
                        "script-only package lacks BuildArch: noarch; "
                        "rpmbuild then builds an empty debuginfo and fails "
                        "(Empty %files file debugfiles.list)"
                    ),
                    rel,
                    line=_line_of(text, "Name:") or _line_of(text, "License:"),
                    # xgettext: no-python-format
                    fix=_(
                        "Add `BuildArch: noarch` and "
                        "`%global debug_package %{nil}` (or run `zfr ize`)."
                    ),
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
                and not covers(lines, e)
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
