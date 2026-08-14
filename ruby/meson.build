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
            echo "0.0.0" # DO NOT MODIFY THIS LINE
        fi
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
ruby = find_program('ruby', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

# Install helper module next to the executable so require_relative works.
common_lib = custom_target(
    'common_lib.rb',
    input: 'src/common_lib.rb',
    output: 'common_lib.rb',
    command: ['cp', '@INPUT@', '@OUTPUT@'],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

app_scripts = [
    'src/some_puff1.rb',
]

foreach script : app_scripts
    base = script.split('/')[-1]
    name = fs.stem(base)
    custom_target(
        name,
        input: script,
        output: name,
        command: [
            'sh',
            '-c', 'cp "$1" "$2" && chmod 755 "$2"',
            '_',
            '@INPUT@',
            '@OUTPUT@',
        ],
        build_by_default: true,
        install: true,
        install_dir: bindir,
        depends: common_lib,
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
