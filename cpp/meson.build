project(
    'zephyr',
    'cpp',
    version: run_command(
        'sh',
        '-c', '''
        v=$(
            command -v zephyr >/dev/null 2>&1 && zephyr version 2>/dev/null || true
        )
        if [ -z "$v" ] && [ -f VERSION ]; then
            v=$(head -n1 VERSION | tr -d '\r')
            v=${v#v}
        fi
        if [ -z "$v" ]; then
            v="0.0.0" # FIXED TO 0.0.0, DO NOT MODIFY
        fi
        printf '%s' "$v"
        ''',
        check: false,
    ).stdout().strip(),
    license: 'AGPL-3.0-or-later',
    default_options: [
        'cpp_std=c++17',
        'warning_level=2',
    ],
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

asciidoctor = find_program('asciidoctor', required: true)
fs = import('fs')

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

config_h = configuration_data()
config_h.set_quoted('PROJECT_VERSION', meson.project_version())
config_h.set_quoted('PROJECT_AUTHOR', project_author)
config_h.set_quoted('PROJECT_EMAIL', project_email)
config_h.set('PROJECT_YEAR', project_year)

configure_file(
    output: 'config.h',
    configuration: config_h,
)

inc = include_directories('src', '.')

app_sources = [
    'src/some_puff1.cpp',
]

common_sources = [
    'src/common_lib.cpp',
]

foreach source : app_sources
    name = fs.stem(source.split('/')[-1])
    executable(
        name,
        [source] + common_sources,
        include_directories: inc,
        install: true,
        install_dir: bindir,
    )
endforeach

bash_files = [
    'some_puff1.bash',
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

custom_target(
    'some_puff1-man',
    input: 'docs/some_puff1.adoc',
    output: 'some_puff1.1',
    command: [
        asciidoctor,
        '-b', 'manpage',
        '-a', 'project-version=' + meson.project_version(),
        '-a', 'project-year=@0@'.format(project_year),
        '-a', 'project-author=' + project_author,
        '-a', 'project-email=' + project_email,
        '-o', '@OUTPUT@',
        '@INPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: mandir / 'man1',
)

subdir('tests')

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

run_target(
    'install-symlinks',
    command: [
        'bash',
        '-euc', '''
            prefix="@0@"
            bindir="@1@"
            datadir="@2@"
            mandir="@3@"
            mkdir -p "$bindir" "$datadir/bash-completion/completions" "$mandir/man1"
            sudo ln -sfn "@BUILD_ROOT@/some_puff1" "$bindir/some_puff1"
            sudo ln -sfn "@BUILD_ROOT@/some_puff1.1" "$mandir/man1/some_puff1.1"
            sudo ln -sfn "@SOURCE_ROOT@/some_puff1.bash" "$datadir/bash-completion/completions/some_puff1"
            printf "Symlinks installed under %s\n" "$prefix"
        '''.format(get_option('prefix'), bindir, datadir, mandir),
    ],
)

run_target(
    'uninstall-symlinks',
    command: [
        'bash',
        '-euc', '''
            for p in \
                "@1@/some_puff1" \
                "@3@/man1/some_puff1.1" \
                "@2@/bash-completion/completions/some_puff1"
            do
                if [ -L "$p" ]; then
                    sudo rm -f "$p"
                    printf "Removed %s\n" "$p"
                else
                    printf "Skipped (not a symlink): %s\n" "$p"
                fi
            done
        '''.format(get_option('prefix'), bindir, datadir, mandir),
    ],
)
