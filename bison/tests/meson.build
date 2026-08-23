fixtures = files(
    'fixtures/hello.sexpr',
    'fixtures/add.sexpr',
    'expected/hello.format',
    'expected/add.format',
    'expected/hello.dump',
    'run_fixtures.sh',
)

test(
    'parser-fixtures',
    find_program('bash'),
    args: [
        meson.current_source_dir() / 'run_fixtures.sh',
        some_puff1_exe.full_path(),
    ],
    workdir: meson.current_source_dir(),
    depends: some_puff1_exe,
)
