# Version is injected by rpm/Makefile via `zfr version`.
# RPM Version cannot contain '-'; use `zfr version -r` (hyphens → '_').
# srcversion is the unsanitized Meson/git version and names the tarball.
%{!?version:%global version 0.0.0}
%{!?srcversion:%global srcversion %{version}}

Name:           zephyr
Version:        %{version}
Release:        1%{?dist}
Summary:        Bash CLI template using bash-shlib

License:        AGPL-3.0-or-later
URL:            https://github.com/lenik/zephyr
Packager:       Lenik <zephyr@bodz.net>
Source0:        %{name}-%{srcversion}.tar.xz

BuildArch:      noarch
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  asciidoctor

Requires:       bash
Requires:       bash-shlib

%description
zephyr is a Meson-based template for small Bash command-line utilities
built with bash-shlib (cliboot). It ships the some_puff1 example script,
AsciiDoc man pages, bash completion, and Debian packaging.

%prep
%setup -q -n %{name}-%{srcversion}

%build
meson setup build \
    --prefix=%{_prefix} \
    --bindir=%{_bindir} \
    --datadir=%{_datadir} \
    --mandir=%{_mandir} \
    --sysconfdir=%{_sysconfdir} \
    --localstatedir=%{_localstatedir} \
    --buildtype=plain
meson compile -C build

%install
meson install -C build --destdir=%{buildroot}

%files
%{_bindir}/some_puff1
%{_datadir}/bash-completion/completions/some_puff1
%{_mandir}/man1/some_puff1.1*
%{_datadir}/doc/%{name}/

%changelog
* Wed Aug 19 2026 Lenik <zephyr@bodz.net>
- Align spec with debian/control (Meson, noarch, AGPL-3.0-or-later).
- Version comes from git describe, the same method meson.build uses.
