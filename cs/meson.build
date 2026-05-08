project(
    'zephyr',
    version: run_command(
        'sh',
        '-c', '''
        v=$(git describe --tags --always --dirty 2>/dev/null || true)
        v=${v#v}
        if [ -n "$v" ]; then
            if [ "${v%.*}" = "$v" ]; then
                v="0.0.0-$v"
            fi
            printf "%s" "$v"
        else
            echo "0.0.0"
        fi
        ''',
        check: false,
    ).stdout().strip(),
    license: 'AGPL-3.0-or-later',
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

fs = import('fs')
dotnet = find_program('dotnet', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
libdir = prefix / get_option('libdir')
localedir = prefix / get_option('localedir')
mandir = prefix / get_option('mandir')
pkgdatadir = datadir / meson.project_name()
pkgdocdir = datadir / 'doc' / meson.project_name()

# Zephyr: .NET class library (no native shared/static link; use ProjectReference)
zephyr_out = meson.current_build_dir() / 'zephyr-lib'
zephyr_csproj = meson.current_source_dir() / 'lib' / 'Zephyr' / 'Zephyr.csproj'
zephyr_buildinfo_subst_path = meson.current_build_dir() / 'BuildInfo.meson.cs'
zephyr_buildinfo_cfg = configuration_data()
zephyr_buildinfo_cfg.set('PROJECT_AUTHOR', project_author)
zephyr_buildinfo_cfg.set('PROJECT_EMAIL', project_email)
zephyr_buildinfo_cfg.set('PROJECT_YEAR', project_year)
zephyr_buildinfo_subst = configure_file(
    input: 'lib/Zephyr/BuildInfo.cs.in',
    output: 'BuildInfo.meson.cs',
    configuration: zephyr_buildinfo_cfg,
)

zephyr_lib_stamp = custom_target(
    'zephyr_lib',
    input: [zephyr_csproj, zephyr_buildinfo_subst, 'lib/Zephyr/common_lib.cs', 'lib/Zephyr/BuildInfo.cs', 'lib/Zephyr/BuildInfo.cs.in'],
    output: 'Zephyr.build.stamp',
    command: [
        'bash',
        '-euc', 'dotnet build "$1" -c Release -o "$2" -p:ZEPHYR_BUILDINFO="$3" && touch "$4"',
        '_',
        '@INPUT0@',
        zephyr_out,
        zephyr_buildinfo_subst_path,
        '@OUTPUT@',
    ],
    build_by_default: true,
)

zephyr_dep = declare_dependency(
    sources: zephyr_lib_stamp,
    variables: {
        'ZEPHYR_CSPROJ': zephyr_csproj,
        'ZEPHYR_DLL': zephyr_out / 'Zephyr.dll',
    },
)
meson.override_dependency('zephyr', zephyr_dep)

resx = [
    'apps/puff1/Resources/Strings.de.resx',
    'apps/puff1/Resources/Strings.eo.resx',
    'apps/puff1/Resources/Strings.fr.resx',
    'apps/puff1/Resources/Strings.it.resx',
    'apps/puff1/Resources/Strings.ja.resx',
    'apps/puff1/Resources/Strings.ko.resx',
    'apps/puff1/Resources/Strings.resx',
    'apps/puff1/Resources/Strings.th.resx',
    'apps/puff1/Resources/Strings.vi.resx',
    'apps/puff1/Resources/Strings.zh-Hans.resx',
    'apps/puff1/Resources/Strings.zh-Hant.resx',
    'apps/puff1/Resources/I18n.cs',
]

# pkg-config: for native toolchains Libs= would be wrong; use data-only metadata + custom vars
pkgconfig = import('pkgconfig')
pkgconfig.generate(
    name: 'Zephyr',
    description: 'Zephyr .NET class library (use dotnet/MSBuild, not -l or Libs:)',
    version: meson.project_version(),
    dataonly: true,
    filebase: 'zephyr',
    variables: {
        'ZEPHYR_CSPROJ': zephyr_csproj,
        'ZEPHYR_DLL': zephyr_out / 'Zephyr.dll',
    },
)

test(
    'cs-smoke',
    dotnet,
    args: [
        'run',
        '--project', meson.project_source_root() / 'tests/TestCommonLib.csproj',
        '-c', 'Release',
    ],
    depends: [zephyr_lib_stamp],
)

# Example app: puff1 (see apps/puff1/)
puff1_name = 'puff1'
puff1_out = meson.current_build_dir() / puff1_name + '.p'
puff1_build = custom_target(
    puff1_name + '_build',
    input: [
        'apps/puff1/Puff1.csproj',
        'apps/puff1/Program.cs',
        'lib/Zephyr/Zephyr.csproj',
        'lib/Zephyr/BuildInfo.cs',
        'lib/Zephyr/common_lib.cs',
    ] + resx,
    output: puff1_name + '.stamp',
    command: [
        'bash',
        '-euc', 'dotnet publish "$1" -c Release -o "$2" >/dev/null && touch "$3"',
        '_',
        '@INPUT0@',
        puff1_out,
        '@OUTPUT@',
    ],
    depends: zephyr_lib_stamp,
    build_by_default: true,
)

custom_target(
    puff1_name,
    input: [puff1_build],
    output: puff1_name,
    command: [
        'bash',
        '-euc', '''
        out="$1"
        cat > "$out" <<'EOF'
#!/usr/bin/env sh
exec dotnet "@0@" "$@"
EOF
        chmod +x "$out"
        '''.format(puff1_out / 'Puff1.dll'),
        '_',
        '@OUTPUT@',
    ],
    depends: puff1_build,
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

bash_files = [
    'puff1.bash',
]

foreach file : bash_files
    name = fs.stem(file)
    install_data(
        file,
        install_dir: datadir / 'bash-completion' / 'completions',
        rename: name,
    )
endforeach

install_data(
    [
        'LICENSE',
        'README.md',
        'README-zh.md',
    ],
    install_dir: pkgdocdir,
)

config_man = configuration_data()
config_man.set('PROJECT_VERSION', meson.project_version())
config_man.set('PROJECT_AUTHOR', project_author)
config_man.set('PROJECT_EMAIL', project_email)
config_man.set('PROJECT_YEAR', project_year)

configure_file(
    input: 'puff1.1.in',
    output: 'puff1.1',
    configuration: config_man,
    install: true,
    install_dir: mandir / 'man1',
)

# look task: list what installed files looks like
# ninja install <tmpdir> && tree <tmpdir> && rm -fr <tmpdir>
run_target(
    'look',
    command: [
        'bash',
        '-euc', '''
            tmpdir=$(mktemp -d)
            DESTDIR=$tmpdir meson install -C "@BUILD_ROOT@"
            tree "$tmpdir"
            rm -fr "$tmpdir"
        ''',
    ],
)

# Fast local debugging against the active installation prefix:
# symlink installed paths to project/build outputs.
run_target(
    'install-symlinks',
    command: [
        'bash',
        '-euc', '''
            prefix="@0@"
            bindir="@1@"
            datadir="@2@"
            localedir="@3@"
            mandir="@4@"

            mkdir -p "$bindir" "$datadir/bash-completion/completions" "$localedir" "$mandir/man1"

            sudo ln -sfn "@BUILD_ROOT@/puff1" "$bindir/puff1"
            sudo ln -sfn "@BUILD_ROOT@/puff1.1" "$mandir/man1/puff1.1"
            sudo ln -sfn "@SOURCE_ROOT@/puff1.bash" "$datadir/bash-completion/completions/puff1"

            printf "Symlinks installed under %s\n" "$prefix"
        '''.format(
            get_option('prefix'), #
            bindir,
            datadir,
            localedir,
            mandir,
        ),
    ],
)

run_target(
    'uninstall-symlinks',
    command: [
        'bash',
        '-euc', '''
            prefix="@0@"
            bindir="@1@"
            datadir="@2@"
            localedir="@3@"
            mandir="@4@"

            for p in \
                "$bindir/puff1" \
                "$mandir/man1/puff1.1" \
                "$datadir/bash-completion/completions/puff1"
            do
                if [ -L "$p" ]; then
                    sudo rm -f "$p"
                    printf "Removed %s\n" "$p"
                else
                    printf "Skipped (not a symlink): %s\n" "$p"
                fi
            done
        '''.format(
            get_option('prefix'), #
            bindir,
            datadir,
            localedir,
            mandir,
        ),
    ],
)