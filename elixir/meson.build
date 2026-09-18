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

elixirc = find_program('elixirc', required: true)
elixir = find_program('elixir', required: true)
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

beam_dir = meson.current_build_dir() / 'ebin'

compile_elixir = custom_target(
    'compile_elixir',
    input: ['src/some_puff1.ex', 'src/commons.ex'],
    output: 'compile_elixir.stamp',
    command: [
        'bash',
        '-euc',
        'mkdir -p "$1"; "$2" -o "$1" "$3" "$4"; touch "$5"',
        '_',
        beam_dir,
        elixirc.full_path(),
        '@INPUT0@',
        '@INPUT1@',
        '@OUTPUT@',
    ],
    build_by_default: true,
)

some_puff1 = custom_target(
    'some_puff1',
    input: [compile_elixir],
    output: 'some_puff1',
    command: [
        'bash',
        '-euc',
        'out="$1"; cat > "$out" <<\'EOF\'\n#!/usr/bin/env sh\nexec "@0@" --no-halt -pa "@1@" -e "SomePuff1.main(System.argv())" -- "$@"\nEOF\nchmod +x "$out"'.format(
            elixir.full_path(),
            beam_dir,
        ),
        '_',
        '@OUTPUT@',
    ],
    depends: compile_elixir,
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

test(
    'elixir-smoke',
    elixir,
    args: [meson.project_source_root() / 'tests/test_commons.exs'],
    depends: compile_elixir,
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
