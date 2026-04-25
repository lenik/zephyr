project(
    'zephyr',
    'rust', # Required by i18n.gettext; no C is compiled in this project.
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
    default_options: [
        'warning_level=0',
    ],
    meson_version: '>=0.60.0',
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

fs = import('fs')

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
localedir = prefix / get_option('localedir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

config_man = configuration_data()
config_man.set('PROJECT_VERSION', meson.project_version())
config_man.set('PROJECT_AUTHOR', project_author)
config_man.set('PROJECT_EMAIL', project_email)
config_man.set('PROJECT_YEAR', project_year)

# Rust binary (release) built with Cargo, installed as puff1
cargo_build = find_program('build-aux/cargo-build.sh', dirs: meson.project_source_root(), required: true)

puff1 = custom_target(
    'puff1',
    output: 'puff1',
    input: 'Cargo.lock',
    depend_files: [
        'Cargo.toml',
        'src/lib.rs',
        'src/main.rs',
    ],
    command: [cargo_build, '@OUTPUT@', meson.project_source_root(), meson.current_build_dir()],
    build_by_default: true,
    install: true,
    install_dir: bindir,
)

bash_files = [
    'puff1.bash',
]

foreach file : bash_files
    name = fs.stem(file)
    install_data(
        file,
        install_dir: datadir / 'bash-completion' / 'completions',
        rename: name,
    )
endforeach

install_data(
    [
        'LICENSE',
        'README.md',
        'README-zh.md',
    ],
    install_dir: pkgdocdir,
)

configure_file(
    input: 'puff1.1.in',
    output: 'puff1.1',
    configuration: config_man,
    install: true,
    install_dir: mandir / 'man1',
)

subdir('po')

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

# Fast local debugging against the active installation prefix:
# symlink installed paths to project/build outputs.
run_target(
    'install-symlinks',
    command: [
        'bash',
        '-euc', '''
            prefix="@0@"
            bindir="@1@"
            datadir="@2@"
            localedir="@3@"
            mandir="@4@"

            mkdir -p "$bindir" "$datadir/bash-completion/completions" "$localedir" "$mandir/man1"

            sudo ln -sfn "@BUILD_ROOT@/puff1" "$bindir/puff1"
            sudo ln -sfn "@BUILD_ROOT@/puff1.1" "$mandir/man1/puff1.1"
            sudo ln -sfn "@SOURCE_ROOT@/puff1.bash" "$datadir/bash-completion/completions/puff1"

            printf "Symlinks installed under %s\n" "$prefix"
        '''.format(
            get_option('prefix'),
            bindir,
            datadir,
            localedir,
            mandir,
        ),
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
            localedir="@3@"
            mandir="@4@"

            for p in \
                "$bindir/puff1" \
                "$mandir/man1/puff1.1" \
                "$datadir/bash-completion/completions/puff1"
            do
                if [ -L "$p" ]; then
                    sudo rm -f "$p"
                    printf "Removed %s\n" "$p"
                else
                    printf "Skipped (not a symlink): %s\n" "$p"
                fi
            done
        '''.format(
            get_option('prefix'),
            bindir,
            datadir,
            localedir,
            mandir,
        ),
    ],
)

env_test = environment()
env_test.set('RUSTC_WRAPPER', '')

test(
    'cargo-test',
    find_program('cargo', required: true),
    args: [
        'test',
        '--locked',
        '--manifest-path',
        meson.project_source_root() / 'Cargo.toml',
        '--target-dir',
        meson.current_build_dir() / 'cargo-test-target',
    ],
    workdir: meson.project_source_root(),
    env: env_test,
    timeout: 300,
)
