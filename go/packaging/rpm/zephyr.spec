# Version is injected by packaging/rpm/Makefile via `zfr version`.
# RPM Version cannot contain '-'; use `zfr version -r` (hyphens → '_').
# srcversion is the unsanitized Meson/git version and names the tarball.
%{!?version:%global version 0.0.0}
%{!?srcversion:%global srcversion %{version}}

Name:           zephyr
Version:        %{version}
Release:        1%{?dist}
Summary:        Go-based CLI project template (example: some_puff1)

License:        AGPL-3.0-or-later
URL:            https://github.com/lenik/zephyr
Packager:       Lenik <zephyr@bodz.net>
Source0:        %{name}-%{srcversion}.tar.xz

BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  golang-go
BuildRequires:  asciidoctor

%description
zephyr is a template for small command-line tools written in Go. It
currently ships the some_puff1 example (a cat-like utility) with Debian
metadata, man page, bash completion, and GNU gettext .po files embedded
in the published binary for offline translations.

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
