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
)

project_author = 'Lenik'
project_email = 'zephyr@bodz.net'
project_year = 2026

nasm = find_program('nasm', required: true)
ld = find_program('ld', required: true)
asciidoctor = find_program('asciidoctor', required: true)

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
mandir = prefix / get_option('mandir')
pkgdocdir = datadir / 'doc' / meson.project_name()

some_puff1_o = custom_target(
    'some_puff1_asm',
    input: 'src/some_puff1.asm',
    output: 'some_puff1.o',
    command: [
        nasm,
        '-f', 'elf64',
        '-I', 'src',
        '-o', '@OUTPUT@',
        '@INPUT@',
    ],
    build_by_default: true,
)

some_puff1_exe = custom_target(
    'some_puff1',
    input: some_puff1_o,
    output: 'some_puff1',
    command: [ld, '-o', '@OUTPUT@', '@INPUT@'],
    build_by_default: true,
    install: true,
    install_dir: bindir,
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

custom_target(
    'some_puff1-man',
    input: 'docs/some_puff1.adoc',
    output: 'some_puff1.1',
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

subdir('tests')

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
            sudo ln -sfn "@BUILD_ROOT@/some_puff1" "$bindir/some_puff1"
            sudo ln -sfn "@BUILD_ROOT@/some_puff1.1" "$mandir/man1/some_puff1.1"
            sudo ln -sfn "@SOURCE_ROOT@/some_puff1.bash" "$datadir/bash-completion/completions/some_puff1"
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
            for p in "$bindir/some_puff1" "$mandir/man1/some_puff1.1" "$datadir/bash-completion/completions/some_puff1"
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
