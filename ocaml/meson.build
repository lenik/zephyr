project(
    'zephyr',
    version: run_command(
        'sh',
        '-c', '''
        v=$(
            command -v zfr >/dev/null 2>&1 && zfr version 2>/dev/null || true
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
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

ocamlfind = find_program('ocamlfind', required: true)
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

src_dir = meson.project_source_root() / 'src'
build_dir = meson.current_build_dir()

some_puff1 = custom_target(
    'some_puff1',
    input: ['src/commons.ml', 'src/some_puff1.ml'],
    output: 'some_puff1',
    command: [
        ocamlfind,
        'ocamlc',
        '-I', src_dir,
        '-o', '@OUTPUT@',
        '@INPUT0@',
        '@INPUT1@',
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

test(
    'ocaml-smoke',
    'bash',
    args: [
        '-euc',
        '''
            set -e
            out="$1"
            test_src="$2"
            commons="$3"
            ocamlfind ocamlc -I "$(dirname "$commons")" -o "$out" "$test_src" "$commons"
            "$out"
            rm -f "$out"
        ''',
        '_',
        build_dir / 'test_commons',
        meson.project_source_root() / 'tests/test_commons.ml',
        src_dir / 'commons.ml',
    ],
)

install_data(
    'some_puff1.bash',
    install_dir: datadir / 'bash-completion' / 'completions',
    rename: 'some_puff1',
)

install_data(
    [
        'LICENSE',
        'README.md',
        'README-zh_CN.md',
    ],
    install_dir: pkgdocdir,
)

custom_target(
    'some_puff1-man',
    input: 'man/some_puff1.adoc',
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
    'posync',
    command: [
        find_program('zfr'),
        'translate',
        '--sync',
        '-C', meson.project_source_root(),
    ],
)

run_target(
    'look',
    command: [
        find_program('zfr'),
        'build',
        '--look',
        '-C', meson.project_source_root(),
        '-b', meson.project_build_root(),
    ],
)
