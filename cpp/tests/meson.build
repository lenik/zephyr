test_exe = executable(
    'common_lib_test',
    [
        'common_lib_test.cpp',
        '../src/common_lib.cpp',
    ],
    include_directories: include_directories('../src'),
    install: false,
)

test('common_lib', test_exe)
