/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.nio.file.Files
import java.nio.file.Path

object commons {
    @Throws(IOException::class)
    fun copyStream(`in`: InputStream, out: OutputStream) {
        val buf = ByteArray(8192)
        while (true) {
            val n = `in`.read(buf)
            if (n == -1) {
                break
            }
            out.write(buf, 0, n)
        }
        out.flush()
    }

    @Throws(IOException::class)
    fun copyFile(file: Path, out: OutputStream) {
        Files.newInputStream(file).use { input ->
            copyStream(input, out)
        }
    }
}
