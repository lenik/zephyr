/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

public final class TestCommons {
    private TestCommons() {}

    public static void main(String[] args) throws Exception {
        commons.AstNode ast = commons.AstNode.list(
            java.util.List.of(
                commons.AstNode.atom("hello"),
                commons.AstNode.atom("world")
            )
        );
        StringBuilder sb = new StringBuilder();
        commons.astFormat(ast, sb, commons.ColorMode.NEVER, 4, 0);
        sb.append('\n');
        String got = sb.toString();
        String want = "(hello\n    world)\n";
        if (!want.equals(got)) {
            throw new IllegalStateException("format mismatch:\n" + got);
        }

        StringBuilder dump = new StringBuilder();
        commons.astDump(ast, dump, commons.ColorMode.NEVER, 0);
        if (!dump.toString().startsWith("list (2)")) {
            throw new IllegalStateException("dump mismatch:\n" + dump);
        }
    }
}
