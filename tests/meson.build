check_dep = dependency('check', required: true)

c_pch = '../' + c_pch
exe_inc = include_directories('../src', '..')

test_sources = [
    'puff1_test.c',
]

foreach test_src : test_sources
    split = test_src.split('/')
    base = split[split.length() - 1]
    dir = fs.parent(test_src)
    stem_test = fs.stem(base)

    if stem_test.endswith('_test')
        stem = stem_test.replace('_test', '')
    elif stem_test.endswith('_unit')
        stem = stem_test.replace('_unit', '')
    else
        continue
    endif

    sibling_dir = '../src' / dir

    # Use 'includes' utility to get implementation dependencies
    # 'includes -e -c test.cpp' returns source files, one per line (not -I include paths)

    use_includes = false
    if use_includes
        includes_result = run_command('includes', '-e', '-c', test_src, check: false)

        impl_deps = []
        if includes_result.returncode() == 0
            # Parse the output: each line is a .c/.cpp file path
            output = includes_result.stdout()
            lines = output.split('\n')
            foreach line : lines
                line = line.strip()
                # Keep non-empty lines that are .c/.cpp files
                if line.endswith('.cpp') or line.endswith('.c')
                    impl_deps += line
                endif
            endforeach
        endif
    else
        impl_deps = []
        # if fs.exists(sibling_dir / stem + '.c')
        #     impl_deps = [sibling_dir / stem + '.c']
        # endif
    endif

    # Create the executable (LOGGER_NAME so program.h and logger.c work in tests)
    test_exe = executable(
        stem,
        test_src,
        impl_deps,
        c_args: c_args,
        c_pch: c_pch,
        include_directories: [sibling_dir, exe_inc],
        link_with: lib_zephyr_static,
        dependencies: [exe_deps, check_dep],
        install: false,
    )

    test(stem, test_exe)
endforeach