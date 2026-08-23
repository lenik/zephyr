test_exe = executable(
    'commons_test',
    [
        'commons_test.cpp',
        '../src/commons.cpp',
    ],
    include_directories: include_directories('../src'),
    install: false,
)

test('commons', test_exe)
