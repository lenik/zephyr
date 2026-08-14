test_exe = executable(
    'common_lib_test',
    [
        'common_lib_test.c',
        '../src/common_lib.c',
    ],
    include_directories: include_directories('../src'),
    install: false,
)

test('common_lib', test_exe)
