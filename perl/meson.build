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
        else
            v="0.0.0" # FIXED TO 0.0.0, DO NOT MODIFY
        fi
        printf '%s' "$v"
        ''',
        check: false,
    ).stdout().strip(),
    license: 'AGPL-3.0-or-later',
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

asciidoctor = find_program('asciidoctor', required: true)
fs = import('fs')
perl = find_program('perl', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

# Install helper module next to the executable so FindBin + lib RealBin works.
common_lib = custom_target(
    'CommonLib.pm',
    input: 'src/CommonLib.pm',
    output: 'CommonLib.pm',
    command: ['cp', '@INPUT@', '@OUTPUT@'],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

app_scripts = [
    'src/some_puff1.pl',
]

foreach script : app_scripts
    base = script.split('/')[-1]
    name = fs.stem(base)
    custom_target(
        name,
        input: script,
        output: name,
        command: [
            perl,
            '-e',
            'use File::Copy qw(copy); copy($ARGV[0], $ARGV[1]) or die $!; chmod 0755, $ARGV[1] or die $!',
            '@INPUT@',
            '@OUTPUT@',
        ],
        build_by_default: true,
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
