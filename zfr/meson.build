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

# Shared GitHub Actions release CI scaffold (create/ize/stdfiles).
install_subdir(
    'share' / 'ci',
    install_dir: pkgdatadir,
    exclude_directories: ['__pycache__'],
)

# Example ~/.config/zfr/scripts/ upload/publish hooks.
install_subdir(
    'share' / 'zfr-scripts',
    install_dir: pkgdatadir / 'zfr-scripts-examples',
    exclude_directories: ['__pycache__'],
)

install_data(
    'src/zfr',
    install_dir: pkgdatadir / 'zfr',
    install_mode: 'rwxr-xr-x',
)

# All top-level *.py under src/ (keeps install complete as modules are added).
_zfr_py_modules = run_command(
    py,
    '-c',
    'from pathlib import Path; import sys\n'
    + 'src = Path(sys.argv[1])\n'
    + 'print("\\n".join(f"src/{p.name}" for p in sorted(src.glob("*.py"))))\n',
    meson.project_source_root() / 'src',
    check: true,
).stdout().strip().split('\n')
install_data(
    _zfr_py_modules,
    install_dir: pkgdatadir / 'zfr',
)

foreach _pkg : [
    'i18n', 'ize', 'lang', 'lint', 'pkg', 'release', 'std', 'translate',
]
    install_subdir(
        'src' / _pkg,
        install_dir: pkgdatadir / 'zfr',
        exclude_directories: ['__pycache__'],
    )
endforeach

paths_cfg = configuration_data()
paths_cfg.set_quoted('PKGDATADIR', pkgdatadir)
paths_cfg.set_quoted('VERSION', meson.project_version())
# Bake the top debian/changelog Date as YYYY-MM-DD for installed --version
# (share/zephyr has VERSION but not debian/changelog).
_release_date = run_command(
    py,
    '-c',
    '''
import re, sys
from email.utils import parsedate_to_datetime
from pathlib import Path
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="ignore")
raw = ""
# Prefer trailer date on the first stanza.
for line in text.splitlines():
    if line.startswith(" -- "):
        m = re.search(r"  ([A-Z][a-z]{2}, .+)$", line)
        if m:
            raw = m.group(1).strip()
        break
if not raw:
    print("", end="")
    raise SystemExit(0)
try:
    print(parsedate_to_datetime(raw).date().isoformat(), end="")
except (TypeError, ValueError, IndexError):
    print("", end="")
''',
    meson.current_source_dir() / 'debian' / 'changelog',
    check: false,
).stdout().strip()
if _release_date == ''
    _release_date = 'unknown'
endif
paths_cfg.set_quoted('RELEASE_DATE', _release_date)
configure_file(
    input: 'src/paths_config.py.in',
    output: 'paths_config.py',
    configuration: paths_cfg,
    install: true,
    install_dir: pkgdatadir / 'zfr',
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
    'zfr-lintsel',
    'zfr-izesel',
    'zfr-comments',
    'zfr-dist',
    'zfr-ize',
    'zfr-i18n',
    'zfr-translate',
    'zfr-shape',
    'zfr-build',
    'zfr-package',
    'zfr-lasterror',
    'zfr-release',
    'zfr-publish',
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

# gettext catalogs for the zfr CLI (domain: zephyr)
subdir('po')

# Man page for zephyr tools (English) plus full-document translations
# under man/<lang>/zfr.adoc (no po4a).
custom_target(
    'zfr-man',
    input: 'man/zfr.adoc',
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
    'uk', 'ur', 'vi', 'zh_CN', 'zh_TW',
]
foreach lang : man_i18n_langs
    man_i18n = custom_target(
        'zfr-man-' + lang,
        input: 'man' / lang / 'zfr.adoc',
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
foreach completion_name : ['zfr', 'zfr-create', 'zfr-rename', 'zfr-add', 'zfr-remove', 'zfr-about', 'zfr-version', 'zfr-lint', 'zfr-lintsel', 'zfr-izesel', 'zfr-comments', 'zfr-dist', 'zfr-ize', 'zfr-i18n', 'zfr-translate', 'zfr-shape', 'zfr-build', 'zfr-package', 'zfr-lasterror', 'zfr-release', 'zfr-publish']
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

# Shared with the monorepo agent rules (../.cursor/rules); not duplicated under zfr/.
foreach rule : ['version.mdc', 'author.mdc', 'translations.mdc', 'proxy.mdc']
    meson.add_install_script(
        'sh',
        '-c',
        'install -D -m644 "$0" "${MESON_INSTALL_DESTDIR_PREFIX}/$1"',
        meson.project_source_root() / '..' / '.cursor' / 'rules' / rule,
        get_option('datadir') / meson.project_name() / '.cursor' / 'rules' / rule,
    )
endforeach

install_data(
    'LICENSE',
    install_dir: pkgdatadir,
)

install_data(
    'LICENSE',
    install_dir: pkgdocdir,
)

foreach doc : ['README.md', 'README-zh_CN.md']
    meson.add_install_script(
        'sh',
        '-c',
        'install -D -m644 "$0" "${MESON_INSTALL_DESTDIR_PREFIX}/$1"',
        meson.project_source_root() / '..' / doc,
        get_option('datadir') / 'doc' / meson.project_name() / doc,
    )
endforeach

run_target(
    'posync',
    command: [
        py,
        files('src/zfr'),
        'translate',
        '--sync',
        '-C', meson.project_source_root(),
    ],
)

run_target(
    'look',
    command: [
        py,
        files('src/zfr'),
        'build',
        '--look',
        '-C', meson.project_source_root(),
        '-b', meson.project_build_root(),
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
