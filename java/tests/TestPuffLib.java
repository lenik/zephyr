/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;

public final class TestPuffLib {
    private TestPuffLib() {}

    public static void main(String[] args) throws Exception {
        ByteArrayInputStream in = new ByteArrayInputStream("alpha\nbeta\n".getBytes(StandardCharsets.UTF_8));
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PuffLib.copyStream(in, out);
        String got = out.toString(StandardCharsets.UTF_8);
        if (!"alpha\nbeta\n".equals(got)) {
            throw new IllegalStateException("copyStream mismatch: " + got);
        }
    }
}
