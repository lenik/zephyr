test(
    'commons',
    find_program('bash'),
    args: [
        '-euc',
        '''
        runtime=""
        for cand in /usr/share/java/antlr4-runtime.jar /usr/share/java/antlr4-runtime-*.jar; do
            if [ -f "$cand" ]; then
                runtime="$cand"
                break
            fi
        done
        work=$(mktemp -d)
        trap 'rm -rf "$work"' EXIT
        "@0@" -encoding UTF-8 -cp "@1@:$runtime" -d "$work" "@2@"
        "@3@" -cp "$work:@1@:$runtime" TestCommons
        '''.format(
            javac.full_path(),
            meson.current_build_dir() / 'some_puff1.jar',
            meson.current_source_dir() / 'TestCommons.java',
            java.full_path(),
        ),
    ],
    depends: some_puff1_jar,
)
