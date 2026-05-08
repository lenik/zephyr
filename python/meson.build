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

py = import('python').find_installation('python3')
fs = import('fs')

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
localedir = prefix / get_option('localedir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

puff1_exe = custom_target(
    'puff1',
    input: 'src/puff1.py',
    output: 'puff1',
    command: [
        py,
        '-c',
        'import os, shutil, sys; shutil.copyfile(sys.argv[1], sys.argv[2]); os.chmod(sys.argv[2], 0o755)',
        '@INPUT@',
        '@OUTPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

common_lib_mod = custom_target(
    'common_lib',
    input: 'src/common_lib.py',
    output: 'common_lib.py',
    command: ['cp', '@INPUT@', '@OUTPUT@'],
    build_by_default: true,
    install: true,
    install_dir: bindir,
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

test(
    'python-unit',
    py,
    args: ['-m', 'unittest', 'discover', '-s', (meson.project_source_root() / 'tests'), '-p', 'test_*.py'],
    env: [
        'PYTHONPATH=' + (meson.project_source_root() / 'src'),
        'ZEPHYR_LOCALEDIR=' + (meson.project_build_root() / 'po'),
    ],
)

run_target(
    'posync',
    command: [
        'bash',
        '-euc', '''
            cd "@SOURCE_ROOT@/po"
            xgettext --from-code=UTF-8 --keyword=_ --language=Python --directory=.. --output=puff1.pot --files-from=POTFILES
            while IFS= read -r lang; do
                [ -n "$lang" ] || continue
                case "$lang" in
                    '#'* ) continue ;;
                esac
                po_file="$lang.po"
                if [ ! -f "$po_file" ]; then
                    msginit --no-translator --input=puff1.pot --locale="$lang" --output-file="$po_file"
                fi
                msgmerge --update --backup=none "$po_file" puff1.pot
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
            prefix="@0@"
            bindir="@1@"
            datadir="@2@"
            mandir="@3@"
            for p in "$bindir/puff1" "$mandir/man1/puff1.1" "$datadir/bash-completion/completions/puff1"
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