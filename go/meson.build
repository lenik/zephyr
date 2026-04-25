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

fs = import('fs')
go = find_program('go', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

puff1_exe = custom_target(
    'puff1',
    input: ['go.mod', 'go.sum'],
    output: 'puff1',
    command: [
        'sh',
        '-euc',
        'cd "@SOURCE_ROOT@" && CGO_ENABLED=0 go build -o "@OUTPUT@" -ldflags "-X main.buildVersion=@0@" ./cmd/puff1'.format(
            meson.project_version()
        ),
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

test(
    'go-unit',
    find_program('bash'),
    args: ['-euc', 'cd "@0@" && CGO_ENABLED=0 go test ./...'.format(meson.project_source_root())],
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
