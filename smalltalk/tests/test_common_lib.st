FileStream fileIn: (File name: 'src/common_lib.st').

| in out got |
in := ReadStream on: 'alpha
beta
'.
out := WriteStream on: String new.
common_lib copyStream: in to: out.
got := out contents.
(got = 'alpha
beta
') ifFalse: [ ObjectMemory quit: 1 ].
ObjectMemory quit: 0.
