# SPDX-License-Identifier: AGPL-3.0-or-later
"""RPM spec rendering."""
from __future__ import annotations

from .util import *  # noqa: F403

def render_spec(root: Path, lang: str, name: str) -> str:
    src, pkg, _ = _control(root)
    desc = pkg.get("Description") or src.get("Description") or name
    summary = desc.split("\n", 1)[0].strip()
    long = desc.split("\n", 1)[1].strip() if "\n" in desc else summary
    long = "\n".join(ln.strip() for ln in long.split("\n"))
    homepage = _homepage(root)
    author, email = _maintainer(root)
    arch = (pkg.get("Architecture") or "any").strip()
    br = _split_deps(src.get("Build-Depends", ""))
    if "meson" not in br:
        br = ["meson", "ninja-build", *br]
    if "asciidoctor" not in br:
        br.append("asciidoctor")
    req = _split_deps(pkg.get("Depends", ""))
    if arch == "all":
        buildarch = (
            "%global debug_package %{nil}\n"
            "BuildArch:      noarch\n"
        )
    else:
        buildarch = ""
    br_block = "\n".join(f"BuildRequires:  {n}" for n in br)
    req_block = "\n".join(f"Requires:       {n}" for n in req)
    if req_block:
        req_block = req_block + "\n"
    files = "\n".join(_spec_files(root, lang, name))
    return (
        "# Version is injected by rpm/Makefile via `zfr version`.\n"
        "# RPM Version cannot contain '-'; use `zfr version -r` "
        "(hyphens → '_').\n"
        "# srcversion is the unsanitized Meson/git version and names the tarball.\n"
        "%{!?version:%global version 0.0.0}\n"
        "%{!?srcversion:%global srcversion %{version}}\n"
        "\n"
        f"Name:           {name}\n"
        "Version:        %{version}\n"
        "Release:        1%{?dist}\n"
        f"Summary:        {summary}\n"
        "\n"
        f"License:        {_AGPL}\n"
        f"URL:            {homepage}\n"
        f"Packager:       {author} <{email}>\n"
        "Source0:        %{name}-%{srcversion}.tar.xz\n"
        "\n"
        f"{buildarch}{br_block}\n"
        f"{req_block}"
        f"\n%description\n{long}\n"
        "\n%prep\n"
        "%setup -q -n %{name}-%{srcversion}\n"
        "\n%build\n"
        "meson setup build \\\n"
        "    --prefix=%{_prefix} \\\n"
        "    --bindir=%{_bindir} \\\n"
        "    --datadir=%{_datadir} \\\n"
        "    --mandir=%{_mandir} \\\n"
        "    --sysconfdir=%{_sysconfdir} \\\n"
        "    --localstatedir=%{_localstatedir} \\\n"
        "    --buildtype=plain\n"
        "meson compile -C build\n"
        "\n%install\n"
        "meson install -C build --destdir=%{buildroot}\n"
        f"\n%files\n{files}\n"
        "\n%changelog\n"
        f"* Thu Aug 20 2026 {author} <{email}>\n"
        "- Align spec with debian/control (Meson, AGPL-3.0-or-later).\n"
        "- Version comes from `zfr version`, the same method meson.build uses.\n"
    )
