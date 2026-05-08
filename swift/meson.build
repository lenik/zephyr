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
            echo "0.0.0"
        fi
        ''',
        check: false,
    ).stdout().strip(),
    license: 'AGPL-3.0-or-later',
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

swiftc = find_program('swiftc', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

puff1 = custom_target(
    'puff1',
    input: ['src/main.swift', 'src/common_lib.swift'],
    output: 'puff1',
    command: [
        swiftc,
        '-O',
        '-o',
        '@OUTPUT@',
        '@INPUT0@',
        '@INPUT1@',
    ],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

swift_test_bin = custom_target(
    'swift-test',
    input: ['tests/TestCommonLib.swift', 'src/common_lib.swift'],
    output: 'swift-test',
    command: [
        swiftc,
        '-O',
        '-o',
        '@OUTPUT@',
        '@INPUT0@',
        '@INPUT1@',
    ],
    build_by_default: true,
)

test(
    'swift-smoke-run',
    swift_test_bin,
    depends: swift_test_bin,
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

# look task: list what installed files looks like
# ninja install <tmpdir> && tree <tmpdir> && rm -fr <tmpdir>
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