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

erlc = find_program('erlc', required: true)
erl = find_program('erl', required: true)
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

beam_dir = meson.current_build_dir() / 'ebin'

compile_erlang = custom_target(
    'compile_erlang',
    input: ['src/some_puff1.erl', 'src/commons.erl'],
    output: 'compile_erlang.stamp',
    command: [
        'bash',
        '-euc',
        'mkdir -p "$1"; "$2" -o "$1" "$3" "$4"; touch "$5"',
        '_',
        beam_dir,
        erlc.full_path(),
        '@INPUT0@',
        '@INPUT1@',
        '@OUTPUT@',
    ],
    build_by_default: true,
)

some_puff1 = custom_target(
    'some_puff1',
    input: [compile_erlang],
    output: 'some_puff1',
    command: [
        'bash',
        '-euc',
        'out="$1"; cat > "$out" <<\'EOF\'\n#!/usr/bin/env sh\nexec "@0@" -pa "@1@" -noshell -s some_puff1 main "$@"\nEOF\nchmod +x "$out"'.format(
            erl.full_path(),
            beam_dir,
        ),
        '_',
        '@OUTPUT@',
    ],
    depends: compile_erlang,
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

test(
    'erlang-smoke',
    erl,
    args: [
        '-pa', beam_dir,
        '-noshell',
        '-eval', 'test_commons:run(), halt().',
    ],
    depends: custom_target(
        'compile_test',
        input: ['tests/test_commons.erl'],
        output: 'compile_test.stamp',
        command: [
            'bash',
            '-euc',
            'mkdir -p "$1"; "$2" -o "$1" "$3"; touch "$4"',
            '_',
            beam_dir,
            erlc.full_path(),
            '@INPUT0@',
            '@OUTPUT@',
        ],
    ),
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
