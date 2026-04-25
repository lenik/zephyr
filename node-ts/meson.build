project(
    'zephyr',
    'c',
    'cpp',
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
        'c_std=c99',
        'warning_level=2',
    ],
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

fs = import('fs')
c = meson.get_compiler('c')
cpp = meson.get_compiler('cpp')

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
libdir = prefix / get_option('libdir')
localedir = prefix / get_option('localedir')
mandir = prefix / get_option('mandir')
pkgdatadir = datadir / meson.project_name()
pkgdocdir = datadir / 'doc' / meson.project_name()

config_h = configuration_data()
config_h.set_quoted('PROJECT_VERSION', meson.project_version())
config_h.set_quoted('PROJECT_AUTHOR', project_author)
config_h.set_quoted('PROJECT_EMAIL', project_email)
config_h.set('PROJECT_YEAR', project_year)

config_h.set_quoted('PREFIX', prefix)
config_h.set_quoted('DATADIR', datadir)
config_h.set_quoted('MANDIR', mandir)
config_h.set_quoted('PKGDATADIR', pkgdatadir)
config_h.set_quoted('LOCALEDIR', localedir)

configure_file(
    output: 'config.h',
    configuration: config_h,
)

bas_c_dep = dependency('bas-c', required: true)
# bas_cpp_dep = dependency('bas-cpp', required: true)

# bas_c_static_dep = dependency('bas-c-static', required: true)
# bas_cpp_static_dep = dependency('bas-cpp-static', required: true)

lib_objects = []

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

    lib_objects += [assets_o]
endif

# Disable all warnings (wx 3.0 and deps are noisy)
nowarn = cpp.get_supported_arguments(['-w', '/w'])
bas_args = ['-DLOGGER_NAME=zephyr', '-DASSETS_NAME=zephyr']

c_pch = 'src/c_pch.h'
c_args = [nowarn, bas_args, '-DTEXT_DOMAIN=zephyr']

lib_inc = [
    include_directories('src'),
]

lib_deps = [
    bas_c_dep,
]

subdir('po')

lib_sources = [
    'src/lib.c',
]

lib_version = meson.project_version().split('-')[0]
lib_soversion = lib_version.split('.')[0]

lib_zephyr = shared_library(
    'zephyr',
    lib_sources,
    lib_objects,
    c_args: c_args,
    c_pch: c_pch,
    include_directories: lib_inc,
    dependencies: lib_deps,
    version: lib_version,
    soversion: lib_soversion,
    install: true,
    install_dir: libdir,
)

lib_zephyr_static = static_library(
    'zephyr',
    lib_sources,
    lib_objects,
    c_args: c_args,
    c_pch: c_pch,
    include_directories: lib_inc,
    dependencies: lib_deps,
)

zephyr_dep = declare_dependency(
    link_with: lib_zephyr,
    include_directories: lib_inc,
)
zephyr_static_dep = declare_dependency(
    link_with: lib_zephyr_static,
    include_directories: lib_inc,
)

meson.override_dependency('zephyr', zephyr_dep)
meson.override_dependency('zephyr-static', zephyr_static_dep)

# ---- pkg-config ----
pkgconfig = import('pkgconfig')
pkgconfig.generate(
    lib_zephyr,
    name: 'zephyr',
    description: 'Zephyr shared library',
    version: meson.project_version(),
    subdirs: 'zephyr',
    requires: ['bas-c'],
)

pkgconfig.generate(
    lib_zephyr_static,
    name: 'zephyr-static',
    description: 'Zephyr static library',
    version: meson.project_version(),
    subdirs: 'zephyr',
    requires: ['bas-c'],
)

# ---- Headers for mesonfmt package (includedir/meson) ----
find_other_cmd = run_command(
    'find',
    'src',
    '-name', '*.h',
    '-o',
    '-name', '*.hpp',
    '-o',
    '-type', 'd',
    '-o',
    '-print',
    check: true,
)
other_files = find_other_cmd.stdout().strip().split('\n')

other_list = []
foreach f : other_files
    other_list += f.substring(4)
endforeach

install_subdir(
    'src',
    install_dir: get_option('includedir'),
    exclude_files: other_list,
    strip_directory: true,
)

app_sources = [
    'src/puff1.c',
]

foreach source : app_sources
    split = source.split('/')
    base = split[-1]
    name = fs.stem(base)
    executable(
        name,
        source,
        c_args: c_args,
        c_pch: c_pch,
        include_directories: lib_inc,
        dependencies: lib_deps,
        link_with: lib_zephyr_static,
        install: true,
        install_dir: bindir,
    )
endforeach

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
            get_option('prefix'), #
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
            get_option('prefix'), #
            bindir,
            datadir,
            localedir,
            mandir,
        ),
    ],
)

subdir('tests')