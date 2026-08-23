/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.nio.charset.StandardCharsets

fun main() {
    val input = "alpha\nbeta\n".toByteArray(StandardCharsets.UTF_8)
    val `in` = ByteArrayInputStream(input)
    val out = ByteArrayOutputStream()
    commons.copyStream(`in`, out)
    val got = out.toString(StandardCharsets.UTF_8)
    check(got == "alpha\nbeta\n") { "copyStream mismatch: $got" }
}
