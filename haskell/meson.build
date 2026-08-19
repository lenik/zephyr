project(
    'zephyr',
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
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

ghc = find_program('ghc', required: true)
runghc = find_program('runghc', required: true)
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

some_puff1 = custom_target(
    'some_puff1',
    input: ['src/Main.hs', 'src/Common_Lib.hs'],
    output: 'some_puff1',
    command: [
        ghc,
        '-O2',
        '-i' + (meson.project_source_root() / 'src'),
        '-odir',
        meson.current_build_dir(),
        '-hidir',
        meson.current_build_dir(),
        '-o',
        '@OUTPUT@',
        '@INPUT0@',
        '@INPUT1@',
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

test(
    'haskell-smoke',
    runghc,
    args: [
        '-i' + (meson.project_source_root() / 'src'),
        meson.project_source_root() / 'tests/TestCommon_Lib.hs',
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
            rg -No 'tr "([^"\\]|\\.)*"' ../src/*.hs | sed 's|^tr |void _z(void){ (void)tr |; s|$|; }|' > "$tmp_c"
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
