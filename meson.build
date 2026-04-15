project(
    'zephyr',
    'c',
    'cpp',
    version: run_command(
        'sh',
        '-c', 'v=$(git describe --tags --always --dirty 2>/dev/null || true); v=${v#v}; [ -n "$v" ] && printf "%s" "$v" || printf "0.0.0"',
        check: false,
    ).stdout().strip(),
    license: 'AGPL-3.0-or-later',
    default_options: [
        'c_std=c99',
        'warning_level=2',
    ],
)
project_author = 'Lenik'
project_email = 'ZEPHYR@bodz.net'
project_year = 2026

fs = import('fs')
c = meson.get_compiler('c')
cpp = meson.get_compiler('cpp')

prefix = get_option('prefix')
datadir = prefix / get_option('datadir')
localedir = prefix / get_option('localedir')
mandir = prefix / get_option('mandir')
pkgdatadir = datadir / meson.project_name()
pkgdocdir = datadir / 'doc' / meson.project_name()

config = configuration_data()
config.set_quoted('PROJECT_VERSION', meson.project_version())
config.set_quoted('PROJECT_AUTHOR', project_author)
config.set_quoted('PROJECT_EMAIL', project_email)
config.set('PROJECT_YEAR', project_year)

config.set_quoted('PREFIX', prefix)
config.set_quoted('DATADIR', datadir)
config.set_quoted('MANDIR', mandir)
config.set_quoted('PKGDATADIR', pkgdatadir)
config.set_quoted('LOCALEDIR', localedir)

configure_file(
    output: 'config.h',
    configuration: config,
)

bas_c_dep = dependency('bas-c', required: true)
# bas_cpp_dep = dependency('bas-cpp', required: true)

# bas_c_static_dep = dependency('bas-c-static', required: true)
# bas_cpp_static_dep = dependency('bas-cpp-static', required: true)

exe_objs = []

# Build assets.zip every time (no file dependency)
assets_dir = meson.current_source_dir() / 'assets'
assets_src = 'src/assets.s'
if fs.exists(assets_dir) and fs.exists(assets_src)
    build_dir = meson.current_build_dir()
    assets_zip = custom_target(
        'assets_zip',
        output: 'assets.zip',
        input: [],
        command: [
            'sh',
            '-c', 'dst=$(readlink -f "@1@"); cd "@0@" && zip -r "$dst" .'.format(assets_dir, '@OUTPUT@'),
        ],
        #build_always : true,
        build_by_default: true,
        install: false,
    )

    # Compile assembly file that embeds assets.zip using .incbin
    # Use configure_file to copy assets.s to build directory
    assets_s = configure_file(
        input: 'src/assets.s',
        output: 'assets.s',
        copy: true,
    )

    # Compile the assembly file (assets.zip will be in the same directory)
    as = find_program('as', required: true)
    assets_o = custom_target(
        'assets_o',
        output: 'assets.o',
        input: [assets_s, assets_zip],
        command: [as, '-o', '@OUTPUT@', '@INPUT0@'],
        depends: assets_zip,
    )

    exe_objs += [assets_o]
endif

# Disable all warnings (wx 3.0 and deps are noisy)
nowarn = cpp.get_supported_arguments(['-w', '/w'])
bas_args = ['-DLOGGER_NAME=ZEPHYR', '-DASSETS_NAME=ZEPHYR']

c_pch = 'src/c_pch.h'
cpp_pch = 'src/cpp_pch.h'

exe_inc = [
    include_directories('src'),
]

exe_deps = [
    bas_c_dep,
]

check_dep = dependency('check', required: true)

executable(
    'zephyr1',
    'src/zephyr1.c',
    exe_objs,
    c_args: nowarn + bas_args,
    c_pch: c_pch,
    include_directories: exe_inc,
    dependencies: exe_deps,
    install: true,
    install_dir: get_option('prefix') / 'bin',
)

unit_sources = [
    'tests/zephyr1_unit.c',
]

foreach unit_src : unit_sources
    unit_base = unit_src.split('/')[-1]
    unit_name = unit_base.replace('.c', '')

    unit_exe = executable(
        unit_name,
        unit_src,
        c_args: nowarn + bas_args,
        c_pch: c_pch,
        include_directories: exe_inc,
        dependencies: exe_deps + [check_dep],
        install: false,
    )

    test(unit_name, unit_exe)
endforeach

install_data(
    'zephyr1.bash',
    install_dir: datadir / 'bash-completion' / 'completions',
    rename: 'zephyr1',
)

install_data(
    [
        'LICENSE',
        'README.md',
        'README-zh.md',
    ],
    install_dir: pkgdocdir,
)

configure_file(
    input: 'zephyr1.1.in',
    output: 'zephyr1.1',
    configuration: config,
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

subdir('po')

run_target(
    'posync',
    command: [
        'bash',
        '-euc', '''
            cd "@SOURCE_ROOT@/po"
            xgettext --from-code=UTF-8 --keyword=_ --language=C --directory=.. --output=zephyr1.pot --files-from=POTFILES
            while IFS= read -r lang; do
                [ -n "$lang" ] || continue
                case "$lang" in
                    '#'* ) continue ;;
                esac
                po_file="$lang.po"
                if [ ! -f "$po_file" ]; then
                    msginit --no-translator --input=zephyr1.pot --locale="$lang" --output-file="$po_file"
                fi
                msgmerge --update --backup=none "$po_file" zephyr1.pot
                msgattrib --no-obsolete --output-file="$po_file" "$po_file"
            done < LINGUAS
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
            bindir="$prefix/bin"
            compdir="@1@/bash-completion/completions"
            man1dir="@2@/man1"

            mkdir -p "$bindir" "$compdir" "$man1dir"

            sudo ln -sfn "@BUILD_ROOT@/zephyr1" "$bindir/zephyr1"
            sudo ln -sfn "@BUILD_ROOT@/zephyr1.1" "$man1dir/zephyr1.1"
            sudo ln -sfn "@SOURCE_ROOT@/zephyr1.bash" "$compdir/zephyr1"

            printf "Symlinks installed under %s\n" "$prefix"
        '''.format(get_option('prefix'), datadir, mandir),
    ],
)

run_target(
    'uninstall-symlinks',
    command: [
        'bash',
        '-euc', '''
            prefix="@0@"
            bindir="$prefix/bin"
            compdir="@1@/bash-completion/completions"
            man1dir="@2@/man1"

            for p in \
                "$bindir/zephyr1" \
                "$man1dir/zephyr1.1" \
                "$compdir/zephyr1"
            do
                if [ -L "$p" ]; then
                    sudo rm -f "$p"
                    printf "Removed %s\n" "$p"
                else
                    printf "Skipped (not a symlink): %s\n" "$p"
                fi
            done
        '''.format(get_option('prefix'), datadir, mandir),
    ],
)
