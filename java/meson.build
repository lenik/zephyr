project(
    'zephyr',
    version: run_command(
        'sh',
        '-c', 'v=$(git describe --tags --always --dirty 2>/dev/null || true); v=${v#v}; [ -n "$v" ] && printf "%s" "$v" || printf "0.0.0"',
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

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

java_sources = [
    'src/Main.java',
    'src/PuffLib.java',
]

puff1_jar = custom_target(
    'puff1_jar',
    input: java_sources,
    output: 'puff1.jar',
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

puff1_exe = custom_target(
    'puff1',
    input: puff1_jar,
    output: 'puff1',
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
    args: ['-cp', puff1_jar, 'Main', '--version'],
)

install_data(
    'puff1.bash',
    install_dir: datadir / 'bash-completion' / 'completions',
    rename: 'puff1',
)

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

run_target(
    'posync',
    command: [
        'bash',
        '-euc', '''
            cd "@SOURCE_ROOT@/po"
            xgettext --from-code=UTF-8 --keyword=tr --language=Java --directory=.. --output=zephyr.pot --files-from=POTFILES
            cp -f zephyr.pot puff1.pot
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
            sudo ln -sfn "@BUILD_ROOT@/puff1" "$bindir/puff1"
            sudo ln -sfn "@BUILD_ROOT@/puff1.1" "$mandir/man1/puff1.1"
            sudo ln -sfn "@SOURCE_ROOT@/puff1.bash" "$datadir/bash-completion/completions/puff1"
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
            for p in "$bindir/puff1" "$mandir/man1/puff1.1" "$datadir/bash-completion/completions/puff1"
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