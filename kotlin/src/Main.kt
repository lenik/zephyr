/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import java.io.IOException
import java.io.PrintStream
import java.nio.file.Path

fun main(args: Array<String>) {
    val projectEmail = "zephyr@bodz.net"
    val projectYear = 2026
    val projectAuthor = "Lenik"

    fun tr(s: String): String = s

    fun usage(out: PrintStream) {
        out.print(tr("Usage: some_puff1 [OPTION]... [FILE]...\n"
                + "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n"
                + "read standard input.\n"))
        out.print("\n")
        out.print("  -v, --verbose      ")
        out.print(tr("repeat for more verbose loggings\n"))
        out.print("  -q, --quiet        ")
        out.print(tr("show less logging messages\n"))
        out.print("  -h, --help         ")
        out.print(tr("display this help and exit\n"))
        out.print("      --version      ")
        out.print(tr("output version information and exit\n"))
        out.print("\n")
        out.print(String.format(tr("Report bugs to: <%s>\n"), projectEmail))
    }

    fun version(out: PrintStream) {
        val v = System.getProperty("zephyr.version", "dev")
        out.printf("some_puff1 %s%n", v)
        out.print(String.format(tr("Copyright (C) %d %s\n"), projectYear, projectAuthor))
        out.print(tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"))
        out.print(tr("This is free software: you are free to change and redistribute it.\n"))
        out.print(tr("This project opposes AI exploitation and AI hegemony.\n"))
        out.print(tr("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.\n"))
        out.print(tr("There is NO WARRANTY, to the extent permitted by law.\n"))
    }

    var verbose = 0
    val files = mutableListOf<String>()
    for (a in args) {
        when (a) {
            "-h", "--help" -> {
                usage(System.out)
                return
            }
            "--version" -> {
                version(System.out)
                return
            }
            "-v", "--verbose" -> verbose++
            "-q", "--quiet" -> verbose = -1
            else -> files.add(a)
        }
    }

    if (verbose > 0) {
        System.err.println("some_puff1: verbose mode enabled")
    }

    if (files.isEmpty()) {
        commons.copyStream(System.`in`, System.out)
        return
    }

    for (f in files) {
        if (f == "-") {
            commons.copyStream(System.`in`, System.out)
        } else {
            try {
                commons.copyFile(Path.of(f), System.out)
            } catch (e: IOException) {
                System.err.printf("some_puff1: %s%n", e.message)
                kotlin.system.exitProcess(1)
            }
        }
    }
}
