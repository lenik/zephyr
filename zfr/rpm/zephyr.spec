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
BuildRequires:  po4a

Requires:       python3
Recommends:     bash-completion

%description
zephyr ships language templates for small command-line utilities under
/usr/share/zephyr/<lang>/ (bash, c, clib, cpp, cpplib, csharp, erlang, go,
haskell, java, perl, python, ruby, rust, smalltalk, swift, typescript), plus
cmdline tools (zfr, zfr-create, zfr-rename, zfr-add, zfr-remove,
zfr-about, zfr-version, zfr-lint, zfr-shape, zfr-dist, zfr-ize,
zfr-release) to create projects, manage puffs (example apps), validate
packaging against zephyr style, build source tarballs, upgrade existing
trees (`zfr ize`), and publish GitHub releases (`zfr release`).

%prep
%setup -q -n %{name}-%{srcversion}

%build
if [ -f meson.build ]; then
    meson_src=.
elif [ -f zfr/meson.build ]; then
    meson_src=zfr
else
    echo "meson.build not found" >&2
    exit 1
fi
meson setup build ${meson_src} \
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
%{_bindir}/zfr
%{_bindir}/zfr-*
%{_datadir}/zephyr/
%{_datadir}/bash-completion/completions/zfr
%{_datadir}/bash-completion/completions/zfr-*
%{_mandir}/man1/zfr.1*
%{_mandir}/*/man1/zfr.1*
%{_datadir}/locale/*/LC_MESSAGES/zfr.mo
%{_datadir}/doc/%{name}/

%changelog
* Thu Aug 20 2026 Lenik <zephyr@bodz.net>
- Initial RPM packaging for the zephyr meta-package (Meson, noarch).
- Version comes from `zfr version`, the same method meson.build uses.
