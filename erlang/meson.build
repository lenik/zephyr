project(
    'zephyr',
    version: run_command(
        'sh',
        '-c',
        'v=$(git describe --tags --always --dirty 2>/dev/null || true); v=${v#v}; [ -n "$v" ] && printf "%s" "$v" || printf "0.0.0"',
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
    input: ['src/some_puff1.erl', 'src/common_lib.erl'],
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
        '-eval', 'test_common_lib:run(), halt().',
    ],
    depends: custom_target(
        'compile_test',
        input: ['tests/test_common_lib.erl'],
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
    'posync',
    command: [
        'bash',
        '-euc', '''
            cd "@SOURCE_ROOT@/po"
            tmp_c=$(mktemp)
            rg -No 'tr\("([^"\\]|\\.)*"\)' ../src/*.erl | sed 's|^tr|void tr|; s|$|;|' > "$tmp_c"
            xgettext --from-code=UTF-8 --keyword=tr --language=C --output=zephyr.pot "$tmp_c"
            rm -f "$tmp_c"
            cp -f zephyr.pot some_puff1.pot
            while IFS= read -r lang; do
                [ -n "$lang" ] || continue
                case "$lang" in
                    '#'* ) continue ;;
                esac
                po_file="$lang.po"
                if [ ! -f "$po_file" ]; then
                    msginit --no-translator --input=zephyr.pot --locale="$lang" --output-file="$po_file"
                fi
                msgmerge --update --backup=none "$po_file" zephyr.pot
                msgattrib --no-obsolete --output-file="$po_file" "$po_file"
            done < LINGUAS
        ''',
    ],
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