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

py = import('python').find_installation('python3')
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdatadir = datadir / meson.project_name()
pkgdocdir = datadir / 'doc' / meson.project_name()

# Language templates live in the parent checkout (bash/, c/, …). Meson
# cannot install_subdir() outside the project source root, so copy at
# install time. Uninstalled wrappers set ZFR_PKGDATADIR to repo_root.
repo_root = run_command(
    py,
    '-c',
    'import os, sys; print(os.path.realpath(sys.argv[1]))',
    meson.project_source_root() / '..',
    check: true,
).stdout().strip()
meson.add_install_script(
    py,
    files('install_templates.py'),
    repo_root,
    get_option('datadir') / meson.project_name(),
)

install_data(
    'VERSION',
    install_dir: pkgdatadir / 'zfr',
)

# Python implementation under <pkgdatadir>/zfr/
install_data(
    [
        'src/zfr',
        'src/zfr-create',
        'src/zfr-rename',
        'src/zfr-add',
        'src/zfr-remove',
        'src/zfr-about',
        'src/zfr-version',
        'src/zfr-lint',
        'src/zfr-dist',
        'src/zfr-ize',
        'src/zfr-shape',
        'src/zfr-release',
    ],
    install_dir: pkgdatadir / 'zfr',
    install_mode: 'rwxr-xr-x',
)

install_subdir(
    'src/zfr_lib',
    install_dir: pkgdatadir / 'zfr',
    exclude_directories: ['__pycache__'],
    exclude_files: ['paths_config.py.in'],
)

paths_cfg = configuration_data()
paths_cfg.set_quoted('PKGDATADIR', pkgdatadir)
configure_file(
    input: 'src/zfr_lib/paths_config.py.in',
    output: 'paths_config.py',
    configuration: paths_cfg,
    install: true,
    install_dir: pkgdatadir / 'zfr' / 'zfr_lib',
)

# Builddir wrappers use the source tree (so ninja && /build/zfr picks up
# current templates + zfr without a DESTDIR install). Bindir wrappers are
# generated in src/ with the installed pkgdatadir.
# Uninstalled: PKGDATADIR = repo root, ZFRDIR = zfr/src
# Installed:   PKGDATADIR = $prefix/share/zephyr, ZFRDIR = zfr
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
    'zfr-shape',
    'zfr-release',
]

uninst_tool_cfg = configuration_data()
uninst_tool_cfg.set('PKGDATADIR', repo_root)
uninst_tool_cfg.set('ZFRDIR', 'zfr/src')
uninst_tool_cfg.set('PYTHON', py.full_path())

inst_tool_cfg = configuration_data()
inst_tool_cfg.set('PKGDATADIR', pkgdatadir)
inst_tool_cfg.set('ZFRDIR', 'zfr')
inst_tool_cfg.set('PYTHON', py.full_path())

foreach name : wrapper_names
    configure_file(
        input: 'src' / (name + '.in'),
        output: name,
        configuration: uninst_tool_cfg,
    )
endforeach

subdir('src')
subdir('tests')

# gettext catalogs for the zfr CLI (domain: zfr)
subdir('po')

# Man page for zephyr tools (English) plus full-document translations
# under docs/<lang>/zfr.adoc (no po4a).
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

man_i18n_langs = [
    'ar', 'bg', 'bn', 'ca', 'cs', 'de', 'el', 'es', 'fr', 'hi', 'hu', 'id',
    'it', 'ja', 'ko', 'nl', 'pl', 'pt', 'ru', 'sv', 'ta', 'te', 'th', 'tr',
    'ur', 'vi', 'zh_CN', 'zh_TW',
]
foreach lang : man_i18n_langs
    man_i18n = custom_target(
        'zfr-man-' + lang,
        input: 'docs' / lang / 'zfr.adoc',
        output: 'zfr.' + lang + '.1',
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
    )
    meson.add_install_script(
        'sh',
        '-c',
        'install -D -m644 "$0" "${MESON_INSTALL_DESTDIR_PREFIX}/$1"',
        man_i18n,
        get_option('mandir') / lang / 'man1' / 'zfr.1',
    )
endforeach

# Bash completion (same script under several command names)
foreach completion_name : ['zfr', 'zfr-create', 'zfr-rename', 'zfr-add', 'zfr-remove', 'zfr-about', 'zfr-version', 'zfr-lint', 'zfr-dist', 'zfr-ize', 'zfr-shape', 'zfr-release']
    install_data(
        'zfr.bash',
        install_dir: datadir / 'bash-completion' / 'completions',
        rename: completion_name,
    )
endforeach

install_data(
    'githooks/pre-commit',
    install_dir: pkgdatadir / 'githooks',
    install_mode: 'rwxr-xr-x',
)

install_data(
    'LICENSE',
    install_dir: pkgdocdir,
)

foreach doc : ['README.md', 'README-zh.md']
    meson.add_install_script(
        'sh',
        '-c',
        'install -D -m644 "$0" "${MESON_INSTALL_DESTDIR_PREFIX}/$1"',
        meson.project_source_root() / '..' / doc,
        get_option('datadir') / 'doc' / meson.project_name() / doc,
    )
endforeach

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
        files('src/zfr'),
        'dist',
        '-b', meson.project_build_root(),
    ],
)
