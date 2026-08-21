# Version is injected by rpm/Makefile via `zfr version`.
# RPM Version cannot contain '-'; use `zfr version -r` (hyphens → '_').
# srcversion is the unsanitized Meson/git version and names the tarball.
%{!?version:%global version 0.0.0}
%{!?srcversion:%global srcversion %{version}}

Name:           zephyr
Version:        %{version}
Release:        1%{?dist}
Summary:        Meson-based CLI project template with example app

License:        AGPL-3.0-or-later
URL:            https://github.com/lenik/zephyr
Packager:       Lenik <zephyr@bodz.net>
Source0:        %{name}-%{srcversion}.tar.xz

BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  ghc
BuildRequires:  gettext
BuildRequires:  asciidoctor

Requires:       ghc

%description
zephyr is a template repository for small Haskell command-line utilities.
It currently ships the some_puff1 example application and Debian packaging
metadata, and includes Haskell-based smoke/unit-test integration.

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
%{_datadir}/locale/*/LC_MESSAGES/zephyr.mo

%changelog
* Thu Aug 20 2026 Lenik <zephyr@bodz.net>
- Align spec with debian/control (Meson, AGPL-3.0-or-later).
- Version comes from `zfr version`, the same method meson.build uses.
