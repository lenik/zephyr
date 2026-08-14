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
        else
            v="0.0.0" # FIXED TO 0.0.0, DO NOT MODIFY
        fi
        printf '%s' "$v"
        ''',
        check: false,
    ).stdout().strip(),
    license: 'AGPL-3.0-or-later',
    meson_version: '>=0.56.0',
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

node = find_program('node', required: true)
asciidoctor = find_program('asciidoctor', required: true)
pandoc = find_program('pandoc', required: true)
makeinfo = find_program('makeinfo', required: true)
tsc = find_program(
    'tsc',
    dirs: [
        meson.project_source_root() / 'node_modules' / '.bin',
    ],
    required: false,
)
if not tsc.found()
    tsc = find_program('tsc', required: true)
endif

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
localedir = prefix / get_option('localedir')
mandir = prefix / get_option('mandir')
infodir = prefix / get_option('infodir')
pkgdatadir = datadir / meson.project_name()
pkgdocdir = datadir / 'doc' / meson.project_name()

subdir('po')

# Compile TypeScript into the build directory, then flatten app JS for install.
# Prefer local (pnpm/npm) tsc + full tsconfig; fall back to system tsc with emit-even-on-error.
js_built = custom_target(
    'zephyr-js',
    input: [
        'src/some_puff1.ts',
        'src/common_lib.ts',
        'src/i18n.ts',
        'tests/common_lib.test.ts',
        'tsconfig.json',
        'tsconfig.meson.json',
    ],
    output: ['some_puff1.js', 'common_lib.js', 'i18n.js'],
    command: [
        'bash',
        '-euc', '''
            src="$1"
            build="$2"
            tscbin="$3"
            out0="$4"
            out1="$5"
            out2="$6"
            if [ -x "$src/node_modules/.bin/tsc" ]; then
                "$src/node_modules/.bin/tsc" -p "$src/tsconfig.json" --outDir "$build/ts_out" --rootDir "$src"
            else
                # System TypeScript (e.g. Debian node-typescript) may lack @types/node;
                # tsconfig.meson.json still emits JS (noEmitOnError=false).
                "$tscbin" -p "$src/tsconfig.meson.json" --outDir "$build/ts_out" --rootDir "$src" || true
                test -f "$build/ts_out/src/some_puff1.js"
                test -f "$build/ts_out/src/common_lib.js"
                test -f "$build/ts_out/src/i18n.js"
            fi
            cp "$build/ts_out/src/some_puff1.js" "$out0"
            cp "$build/ts_out/src/common_lib.js" "$out1"
            cp "$build/ts_out/src/i18n.js" "$out2"
        ''',
        '_',
        meson.project_source_root(),
        meson.current_build_dir(),
        tsc.full_path(),
        '@OUTPUT0@',
        '@OUTPUT1@',
        '@OUTPUT2@',
    ],
    build_by_default: true,
    install: true,
    install_dir: pkgdatadir,
)

# Stage production node_modules (classic npm layout) beside build outputs.
# ESM resolves packages from adjacent/ancestor node_modules (NODE_PATH is ignored).
npm = find_program('npm', required: true)
node_modules_prod = custom_target(
    'node-modules-prod',
    input: ['package.json', 'scripts/prepare-node-modules.sh'],
    output: 'node_modules.stamp',
    command: [
        'bash',
        '-euc', '''
            "$1" "$2" "$3/node_modules_prod"
            rm -rf "$3/node_modules"
            cp -a "$3/node_modules_prod/node_modules" "$3/node_modules"
            touch "$4"
        ''',
        '_',
        meson.project_source_root() / 'scripts' / 'prepare-node-modules.sh',
        meson.project_source_root(),
        meson.current_build_dir(),
        '@OUTPUT@',
    ],
    build_by_default: true,
)

# Build-tree launcher (node_modules lives next to some_puff1.js in the build dir).
some_puff1_local = custom_target(
    'some_puff1',
    input: 'src/some_puff1.sh.in',
    output: 'some_puff1',
    command: [
        'bash',
        '-euc', '''
            sed -e "s|@ENTRYPOINT@|$1|g" -e "s|@NODE_PATH@||g" "$2" > "$3"
            chmod +x "$3"
        ''',
        '_',
        meson.current_build_dir() / 'some_puff1.js',
        '@INPUT@',
        '@OUTPUT@',
    ],
    depends: [js_built, node_modules_prod],
    build_by_default: true,
)

# Installed launcher; node_modules is installed beside some_puff1.js under pkgdatadir.
some_puff1_install_conf = configuration_data()
some_puff1_install_conf.set('ENTRYPOINT', pkgdatadir / 'some_puff1.js')
some_puff1_install_conf.set('NODE_PATH', '')
some_puff1_install_sh = configure_file(
    input: 'src/some_puff1.sh.in',
    output: 'some_puff1.install.sh',
    configuration: some_puff1_install_conf,
)
install_data(
    some_puff1_install_sh,
    install_dir: bindir,
    rename: 'some_puff1',
    install_mode: 'rwxr-xr-x',
)

meson.add_install_script(
    'bash',
    '-euc', '''
        src="$1/node_modules"
        dest="${DESTDIR:-}$2/node_modules"
        mkdir -p "$dest"
        cp -a "$src/." "$dest/"
    ''',
    '_',
    meson.current_build_dir(),
    pkgdatadir,
)

test(
    'node-unit',
    node,
    args: [
        '--test',
        meson.current_build_dir() / 'ts_out' / 'tests' / 'common_lib.test.js',
        meson.current_build_dir() / 'ts_out' / 'tests' / 'i18n.test.js',
    ],
    depends: [js_built],
    env: [
        'ZEPHYR_LOCALEDIR=' + (meson.project_build_root() / 'po'),
        'LANGUAGE=zh_CN',
        'LANG=zh_CN.UTF-8',
    ],
)

test(
    'some_puff1-i18n-zh-CN',
    find_program('bash'),
    args: [
        '-euc',
        'out="$("$1" -h)"; printf "%s\n" "$out"; printf "%s\n" "$out" | grep -q "用法"',
        '_',
        meson.current_build_dir() / 'some_puff1',
    ],
    depends: [js_built, some_puff1_local],
    env: [
        'ZEPHYR_LOCALEDIR=' + (meson.project_build_root() / 'po'),
        'LANGUAGE=zh_CN',
        'LANG=zh_CN.UTF-8',
    ],
)

install_data(
    'some_puff1.bash',
    install_dir: datadir / 'bash-completion' / 'completions',
    rename: 'some_puff1',
)

install_data(
    [
        'LICENSE',
        'README.md',
        'README-zh.md',
    ],
    install_dir: pkgdocdir,
)

# Man + info pages from AsciiDoctor (manpage backend + HTML→Texinfo→makeinfo).
docs_built = custom_target(
    'some_puff1-docs',
    input: [
        'docs/some_puff1.adoc',
        'scripts/build-docs.sh',
    ],
    output: ['some_puff1.1', 'some_puff1.info'],
    command: [
        meson.project_source_root() / 'scripts' / 'build-docs.sh',
        '@INPUT0@',
        meson.current_build_dir(),
        meson.project_version(),
        project_year.to_string(),
        project_author,
        project_email,
    ],
    build_by_default: true,
    install: true,
    install_dir: [mandir / 'man1', infodir],
)

# Ensure doc tools were found (used by scripts/build-docs.sh on PATH).
assert(asciidoctor.found())
assert(pandoc.found())
assert(makeinfo.found())


run_target(
    'posync',
    command: [
        'bash',
        '-euc', '''
            cd "@SOURCE_ROOT@/po"
            xgettext --from-code=UTF-8 --keyword=_ --language=JavaScript --directory=.. --output=zephyr.pot --files-from=POTFILES
            cp -f zephyr.pot some_puff1.pot
            while IFS= read -r lang; do
                [ -n "$lang" ] || continue
                case "$lang" in
                    '#'* ) continue ;;
                esac
                po_file="$lang.po"
                if [ ! -f "$po_file" ]; then
                    msginit --no-translator --input=zephyr.pot --locale="$lang" --output-file="$po_file"
                fi
                msgmerge --update --backup=none "$po_file" zephyr.pot
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
            pkgdatadir="@3@"
            mandir="@4@"
            infodir="@5@"

            mkdir -p "$bindir" "$datadir/bash-completion/completions" "$pkgdatadir" "$mandir/man1" "$infodir"

            sudo ln -sfn "@BUILD_ROOT@/some_puff1" "$bindir/some_puff1"
            sudo ln -sfn "@BUILD_ROOT@/some_puff1.js" "$pkgdatadir/some_puff1.js"
            sudo ln -sfn "@BUILD_ROOT@/common_lib.js" "$pkgdatadir/common_lib.js"
            sudo ln -sfn "@BUILD_ROOT@/i18n.js" "$pkgdatadir/i18n.js"
            sudo ln -sfn "@BUILD_ROOT@/some_puff1.1" "$mandir/man1/some_puff1.1"
            sudo ln -sfn "@BUILD_ROOT@/some_puff1.info" "$infodir/some_puff1.info"
            sudo ln -sfn "@SOURCE_ROOT@/some_puff1.bash" "$datadir/bash-completion/completions/some_puff1"

            printf "Symlinks installed under %s\n" "$prefix"
        '''.format(
            get_option('prefix'),
            bindir,
            datadir,
            pkgdatadir,
            mandir,
            infodir,
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
            pkgdatadir="@3@"
            mandir="@4@"
            infodir="@5@"

            for p in \
                "$bindir/some_puff1" \
                "$pkgdatadir/some_puff1.js" \
                "$pkgdatadir/common_lib.js" \
                "$pkgdatadir/i18n.js" \
                "$mandir/man1/some_puff1.1" \
                "$infodir/some_puff1.info" \
                "$datadir/bash-completion/completions/some_puff1"
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
            pkgdatadir,
            mandir,
            infodir,
        ),
    ],
)
