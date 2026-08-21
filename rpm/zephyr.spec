# Version is injected by rpm/Makefile via `zfr version`.
# RPM Version cannot contain '-'; use `zfr version -r` (hyphens → '_').
# srcversion is the unsanitized Meson/git version and names the tarball.
%{!?version:%global version 0.0.0}
%{!?srcversion:%global srcversion %{version}}

Name:           zephyr
Version:        %{version}
Release:        1%{?dist}
Summary:        Multi-language CLI project templates and helper tools

License:        AGPL-3.0-or-later
URL:            https://github.com/lenik/zephyr
Packager:       Lenik <zephyr@bodz.net>
Source0:        %{name}-%{srcversion}.tar.xz

BuildArch:      noarch
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  python3
BuildRequires:  asciidoctor

Requires:       python3
Recommends:     bash-completion

%description
zephyr ships language templates for small command-line utilities under
/usr/share/zephyr/<lang>/ (bash, c, clib, cpp, cpplib, csharp, erlang, go,
haskell, java, perl, python, ruby, rust, smalltalk, swift, typescript), plus
cmdline tools (zephyr, zephyr-create, zephyr-rename, zephyr-add, zephyr-remove,
zephyr-about, zephyr-version, zephyr-lint, zephyr-dist, zephyr-ize) to create
projects, manage puffs (example apps), validate packaging against zephyr style,
build source tarballs, and upgrade existing trees (`zephyr ize`).

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
%{_bindir}/zephyr
%{_bindir}/zephyr-*
%{_datadir}/zephyr/
%{_datadir}/bash-completion/completions/zephyr
%{_datadir}/bash-completion/completions/zephyr-*
%{_mandir}/man1/zephyr.1*
%{_datadir}/doc/%{name}/

%changelog
* Thu Aug 20 2026 Lenik <zephyr@bodz.net>
- Initial RPM packaging for the zephyr meta-package (Meson, noarch).
- Version comes from `zfr version`, the same method meson.build uses.
