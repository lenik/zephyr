FileStream fileIn: (File name: 'src/common_lib.st').

Object subclass: SomePuff1 [
    SomePuff1 class >> tr: s [ ^s ]

    SomePuff1 class >> usage [
        stdout nextPutAll: (self tr: 'Usage: some_puff1 [OPTION]... [FILE]...'); nl.
        stdout nextPutAll: (self tr: 'Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,'); nl.
        stdout nextPutAll: (self tr: 'read standard input.'); nl; nl.
        stdout nextPutAll: '  -v, --verbose      '; nextPutAll: (self tr: 'repeat for more verbose loggings'); nl.
        stdout nextPutAll: '  -q, --quiet        '; nextPutAll: (self tr: 'show less logging messages'); nl.
        stdout nextPutAll: '  -h, --help         '; nextPutAll: (self tr: 'display this help and exit'); nl.
        stdout nextPutAll: '      --version      '; nextPutAll: (self tr: 'output version information and exit'); nl; nl.
        stdout nextPutAll: 'Report bugs to: <zephyr@bodz.net>'; nl.
    ]

    SomePuff1 class >> versionInfo [
        stdout nextPutAll: 'some_puff1 dev'; nl.
        stdout nextPutAll: (self tr: 'Copyright (C) 2026 Lenik'); nl.
        stdout nextPutAll: (self tr: 'License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>'); nl.
        stdout nextPutAll: (self tr: 'This is free software: you are free to change and redistribute it.'); nl.
        stdout nextPutAll: (self tr: 'This project opposes AI exploitation and AI hegemony.'); nl.
        stdout nextPutAll: (self tr: 'This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.'); nl.
        stdout nextPutAll: (self tr: 'There is NO WARRANTY, to the extent permitted by law.'); nl.
    ]

    SomePuff1 class >> run: args [
        ((args includes: '-h') or: [ args includes: '--help' ]) ifTrue: [ self usage. ObjectMemory quit: 0 ].
        (args includes: '--version') ifTrue: [ self versionInfo. ObjectMemory quit: 0 ].
        args isEmpty ifTrue: [ common_lib copyStream: stdin to: stdout. ObjectMemory quit: 0 ].
        args do: [ :a |
            (a = '-') ifTrue: [
                common_lib copyStream: stdin to: stdout
            ] ifFalse: [
                [ common_lib copyFile: a to: stdout ]
                    on: SystemExceptions.FileError
                    do: [ :ex | stderr nextPutAll: 'some_puff1: '; nextPutAll: ex messageText; nl. ObjectMemory quit: 1 ]
            ]
        ].
        ObjectMemory quit: 0.
    ]
]

SomePuff1 run: Smalltalk arguments.
