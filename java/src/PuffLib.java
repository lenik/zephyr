/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;

public final class PuffLib {
    private PuffLib() {}

    public static void copyStream(InputStream in, OutputStream out) throws IOException {
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) != -1) {
            out.write(buf, 0, n);
        }
        out.flush();
    }

    public static void copyFile(Path file, OutputStream out) throws IOException {
        try (InputStream in = Files.newInputStream(file)) {
            copyStream(in, out);
        }
    }
}
