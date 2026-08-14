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

javac = find_program('javac', required: true)
jar = find_program('jar', required: true)
java = find_program('java', required: true)
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

java_sources = [
    'src/Main.java',
    'src/common_lib.java',
]

some_puff1_jar = custom_target(
    'some_puff1_jar',
    input: java_sources,
    output: 'some_puff1.jar',
    command: [
        'bash',
        '-euc',
        'classes="$1"; src0="$2"; src1="$3"; out="$4"; rm -rf "$classes"; mkdir -p "$classes"; "@0@" -encoding UTF-8 -d "$classes" "$src0" "$src1"; "@1@" --create --file "$out" -C "$classes" .'.format(
            javac.full_path(),
            jar.full_path(),
        ),
        '_',
        '@PRIVATE_DIR@/classes',
        '@INPUT0@',
        '@INPUT1@',
        '@OUTPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: datadir / meson.project_name(),
)

some_puff1_exe = custom_target(
    'some_puff1',
    input: some_puff1_jar,
    output: 'some_puff1',
    command: [
        'bash',
        '-euc',
        'printf "%s\n" "#!/usr/bin/env sh" "exec \"@0@\" -cp \"@INPUT@\" Main \"$@\"" > "@OUTPUT@"; chmod +x "@OUTPUT@"'.format(
            java.full_path()
        ),
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

test(
    'java-smoke',
    java,
    args: ['-cp', some_puff1_jar, 'Main', '--version'],
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
            xgettext --from-code=UTF-8 --keyword=tr --language=Java --directory=.. --output=zephyr.pot --files-from=POTFILES
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
            bindir="@0@"
            datadir="@1@"
            mandir="@2@"
            for p in "$bindir/some_puff1" "$mandir/man1/some_puff1.1" "$datadir/bash-completion/completions/some_puff1"
            do
                if [ -L "$p" ]; then
                    sudo rm -f "$p"
                    printf "Removed %s\n" "$p"
                else
                    printf "Skipped (not a symlink): %s\n" "$p"
                fi
            done
        '''.format(bindir, datadir, mandir),
    ],
)
