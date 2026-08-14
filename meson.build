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
            echo "1.1.1"
        fi
        ''',
        check: false,
    ).stdout().strip(),
    license: 'AGPL-3.0-or-later',
    meson_version: '>=0.61.0',
)

fs = import('fs')
py = import('python').find_installation('python3')

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
pkgdatadir = datadir / meson.project_name()
pkgdocdir = datadir / 'doc' / meson.project_name()

template_langs = [
    'c',
    'cs',
    'erlang',
    'go',
    'haskell',
    'java',
    'python',
    'rust',
    'smalltalk',
    'swift',
    'typescript',
]

exclude_dirs = [
    '.cache',
    '.cursor',
    '.git',
    '.hg',
    '.svn',
    '.vscode',
    '__pycache__',
    'bin',
    'build',
    'cargo-target',
    'dist',
    'meson-info',
    'meson-logs',
    'meson-private',
    'node_modules',
    'obj',
    'target',
]

exclude_files = [
    'CLAUDE.md',
]

foreach lang : template_langs
    if fs.is_dir(lang)
        install_subdir(
            lang,
            install_dir: pkgdatadir,
            exclude_directories: exclude_dirs,
            exclude_files: exclude_files,
        )
    endif
endforeach

# Python implementation under <pkgdatadir>/tools/
install_data(
    [
        'tools/zephyr',
        'tools/zephyr-rename',
        'tools/zephyr-add',
        'tools/zephyr-remove',
    ],
    install_dir: pkgdatadir / 'tools',
    install_mode: 'rwxr-xr-x',
)

install_data(
    [
        'tools/zephyr_lib/__init__.py',
        'tools/zephyr_lib/commands.py',
    ],
    install_dir: pkgdatadir / 'tools' / 'zephyr_lib',
)

paths_cfg = configuration_data()
paths_cfg.set_quoted('PKGDATADIR', pkgdatadir)
configure_file(
    input: 'tools/zephyr_lib/paths_config.py.in',
    output: 'paths_config.py',
    configuration: paths_cfg,
    install: true,
    install_dir: pkgdatadir / 'tools' / 'zephyr_lib',
)

# PATH wrappers in bindir
tool_cfg = configuration_data()
tool_cfg.set('PKGDATADIR', pkgdatadir)
tool_cfg.set('PYTHON', py.full_path())

foreach name : ['zephyr', 'zephyr-rename', 'zephyr-add', 'zephyr-remove']
    configure_file(
        input: 'tools' / (name + '.in'),
        output: name,
        configuration: tool_cfg,
        install: true,
        install_dir: bindir,
        install_mode: 'rwxr-xr-x',
    )
endforeach

install_data(
    'LICENSE',
    install_dir: pkgdocdir,
)

run_target(
    'look',
    command: [
        'bash',
        '-euc', '''
            tmpdir=$(mktemp -d)
            DESTDIR=$tmpdir meson install -C "@BUILD_ROOT@"
            tree -L 6 -I po "$tmpdir" 2>/dev/null || (cd "$tmpdir" && find -maxdepth 6 -name po -prune -o -print)
        ''',
    ],
)
