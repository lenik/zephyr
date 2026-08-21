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
    meson_version: '>=0.61.0',
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

fs = import('fs')
py = import('python').find_installation('python3')
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdatadir = datadir / meson.project_name()
pkgdocdir = datadir / 'doc' / meson.project_name()

template_langs = [
    'bash',
    'c',
    'clib',
    'cpp',
    'cpplib',
    'csharp',
    'erlang',
    'go',
    'haskell',
    'java',
    'perl',
    'python',
    'ruby',
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
    'rpmbuild',
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
        'tools/zfr',
        'tools/zfr-create',
        'tools/zfr-rename',
        'tools/zfr-add',
        'tools/zfr-remove',
        'tools/zfr-about',
        'tools/zfr-version',
        'tools/zfr-lint',
        'tools/zfr-dist',
        'tools/zfr-ize',
    ],
    install_dir: pkgdatadir / 'tools',
    install_mode: 'rwxr-xr-x',
)

install_data(
    [
        'tools/zfr_lib/__init__.py',
        'tools/zfr_lib/commands.py',
        'tools/zfr_lib/about.py',
        'tools/zfr_lib/csr.py',
        'tools/zfr_lib/lint.py',
        'tools/zfr_lib/dist.py',
        'tools/zfr_lib/ize.py',
    ],
    install_dir: pkgdatadir / 'tools' / 'zfr_lib',
)

paths_cfg = configuration_data()
paths_cfg.set_quoted('PKGDATADIR', pkgdatadir)
configure_file(
    input: 'tools/zfr_lib/paths_config.py.in',
    output: 'paths_config.py',
    configuration: paths_cfg,
    install: true,
    install_dir: pkgdatadir / 'tools' / 'zfr_lib',
)

# Builddir wrappers use the source tree (so ninja && ./build/zfr picks up
# current templates + tools without a DESTDIR install). Bindir wrappers are
# generated in tools/ with the installed pkgdatadir.
wrapper_names = [
    'zfr',
    'zfr-create',
    'zfr-rename',
    'zfr-add',
    'zfr-remove',
    'zfr-about',
    'zfr-version',
    'zfr-lint',
    'zfr-dist',
    'zfr-ize',
]

uninst_tool_cfg = configuration_data()
uninst_tool_cfg.set('PKGDATADIR', meson.project_source_root())
uninst_tool_cfg.set('PYTHON', py.full_path())

inst_tool_cfg = configuration_data()
inst_tool_cfg.set('PKGDATADIR', pkgdatadir)
inst_tool_cfg.set('PYTHON', py.full_path())

foreach name : wrapper_names
    configure_file(
        input: 'tools' / (name + '.in'),
        output: name,
        configuration: uninst_tool_cfg,
    )
endforeach

subdir('tools')
subdir('tests')

# Man page for zephyr tools
custom_target(
    'zfr-man',
    input: 'docs/zfr.adoc',
    output: 'zfr.1',
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

# Bash completion (same script under several command names)
foreach completion_name : ['zfr', 'zfr-create', 'zfr-rename', 'zfr-add', 'zfr-remove', 'zfr-about', 'zfr-version', 'zfr-lint', 'zfr-dist', 'zfr-ize']
    install_data(
        'tools/zfr.bash',
        install_dir: datadir / 'bash-completion' / 'completions',
        rename: completion_name,
    )
endforeach

install_data(
    '.githooks/pre-commit',
    install_dir: pkgdatadir / 'githooks',
    install_mode: 'rwxr-xr-x',
)

install_data(
    [
        'LICENSE',
        'README.md',
        'README-zh.md',
    ],
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

# Meson reserves the ninja target name `dist`; srcdist reuses `zfr dist`.
run_target(
    'srcdist',
    command: [
        py,
        files('tools/zfr'),
        'dist',
        '-b', meson.project_build_root(),
    ],
)
