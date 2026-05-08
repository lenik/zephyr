import Foundation

func tr(_ s: String) -> String { s }

let projectAuthor = "Lenik"
let projectEmail = "zephyr@bodz.net"
let projectYear = 2026

func usage() {
    FileHandle.standardOutput.write(Data(tr("Usage: puff1 [OPTION]... [FILE]...\n").utf8))
    FileHandle.standardOutput.write(Data(tr("Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n").utf8))
    FileHandle.standardOutput.write(Data(tr("read standard input.\n\n").utf8))
    FileHandle.standardOutput.write(Data("  -v, --verbose      ".utf8))
    FileHandle.standardOutput.write(Data(tr("repeat for more verbose loggings\n").utf8))
    FileHandle.standardOutput.write(Data("  -q, --quiet        ".utf8))
    FileHandle.standardOutput.write(Data(tr("show less logging messages\n").utf8))
    FileHandle.standardOutput.write(Data("  -h, --help         ".utf8))
    FileHandle.standardOutput.write(Data(tr("display this help and exit\n").utf8))
    FileHandle.standardOutput.write(Data("      --version      ".utf8))
    FileHandle.standardOutput.write(Data(tr("output version information and exit\n\n").utf8))
    FileHandle.standardOutput.write(Data("Report bugs to: <\(projectEmail)>\n".utf8))
}

func versionInfo() {
    let lines = [
        "puff1 dev",
        tr("Copyright (C) \(projectYear) \(projectAuthor)"),
        tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>"),
        tr("This is free software: you are free to change and redistribute it."),
        tr("This project opposes AI exploitation and AI hegemony."),
        tr("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing."),
        tr("There is NO WARRANTY, to the extent permitted by law."),
    ]
    for line in lines {
        FileHandle.standardOutput.write(Data((line + "\n").utf8))
    }
}

let args = Array(CommandLine.arguments.dropFirst())
if args.contains("-h") || args.contains("--help") {
    usage()
    exit(0)
}
if args.contains("--version") {
    versionInfo()
    exit(0)
}

let verbose = args.contains("-v") || args.contains("--verbose")
let files = args.filter { !["-v", "--verbose", "-q", "--quiet"].contains($0) }
if verbose {
    FileHandle.standardError.write(Data("puff1: verbose mode enabled\n".utf8))
}

do {
    if files.isEmpty {
        try common_lib.copyStream(FileHandle.standardInput, FileHandle.standardOutput)
    } else {
        for f in files {
            if f == "-" {
                try common_lib.copyStream(FileHandle.standardInput, FileHandle.standardOutput)
            } else {
                try common_lib.copyFile(f, FileHandle.standardOutput)
            }
        }
    }
    exit(0)
} catch {
    FileHandle.standardError.write(Data("puff1: \(error)\n".utf8))
    exit(1)
}
