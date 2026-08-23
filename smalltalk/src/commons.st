Object subclass: #commons [
    commons class >> copyFile: path to: out [
        | in |
        in := FileStream open: path mode: FileStream read.
        [ self copyStream: in to: out ] ensure: [ in close ].
    ]

    commons class >> copyStream: in to: out [
        [ in atEnd ] whileFalse: [
            out nextPutAll: (in next: 65536)
        ].
    ]
]
