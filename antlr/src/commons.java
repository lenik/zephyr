/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class commons {
    public enum ColorMode {
        AUTO,
        ALWAYS,
        NEVER
    }

    public static final class AstNode {
        public final boolean list;
        public final String atom;
        public final List<AstNode> children;

        private AstNode(boolean list, String atom, List<AstNode> children) {
            this.list = list;
            this.atom = atom;
            this.children = children;
        }

        public static AstNode atom(String text) {
            return new AstNode(false, text, List.of());
        }

        public static AstNode list(List<AstNode> children) {
            return new AstNode(true, null, List.copyOf(children));
        }
    }

    private commons() {}

    public static ColorMode parseColorMode(String text) {
        if (text == null || text.isEmpty() || "auto".equals(text)) {
            return ColorMode.AUTO;
        }
        if ("always".equals(text)) {
            return ColorMode.ALWAYS;
        }
        return ColorMode.NEVER;
    }

    private static boolean colorEnabled(ColorMode mode, OutputStream out) {
        return switch (mode) {
            case NEVER -> false;
            case ALWAYS -> true;
            case AUTO -> System.console() != null || out instanceof java.io.FileOutputStream;
        };
    }

    public static AstNode fromParseTree(SomePuff1Parser.SexprContext ctx) {
        if (ctx.ATOM() != null) {
            return AstNode.atom(ctx.ATOM().getText());
        }
        List<AstNode> kids = new ArrayList<>();
        for (SomePuff1Parser.SexprContext child : ctx.sexpr()) {
            kids.add(fromParseTree(child));
        }
        return AstNode.list(kids);
    }

    public static void astDump(AstNode node, Appendable out, ColorMode color, int indent) throws IOException {
        if (node == null) {
            return;
        }
        for (int i = 0; i < indent; i++) {
            out.append("  ");
        }
        if (node.list) {
            if (colorEnabled(color, System.out)) {
                out.append("\u001B[35mlist\u001B[0m (").append(Integer.toString(node.children.size())).append(")\n");
            } else {
                out.append("list (").append(Integer.toString(node.children.size())).append(")\n");
            }
            for (AstNode child : node.children) {
                astDump(child, out, color, indent + 1);
            }
        } else {
            if (colorEnabled(color, System.out)) {
                out.append("\u001B[35matom\u001B[0m \"").append(node.atom).append("\"\n");
            } else {
                out.append("atom \"").append(node.atom).append("\"\n");
            }
        }
    }

    public static void astFormat(
        AstNode node,
        Appendable out,
        ColorMode color,
        int indentSize,
        int level
    ) throws IOException {
        if (node == null) {
            return;
        }
        if (!node.list) {
            if (colorEnabled(color, System.out)) {
                out.append("\u001B[33m").append(node.atom).append("\u001B[0m");
            } else {
                out.append(node.atom);
            }
            return;
        }

        out.append('(');
        if (node.children.isEmpty()) {
            out.append(')');
            return;
        }

        for (int i = 0; i < node.children.size(); i++) {
            if (i > 0) {
                out.append('\n');
                out.append(" ".repeat((level + 1) * indentSize));
            } else if (node.children.size() == 1) {
                out.append(' ');
            }
            astFormat(node.children.get(i), out, color, indentSize, level + 1);
        }

        if (node.children.size() == 1) {
            out.append(' ');
        }
        out.append(')');
    }

    public static String readAll(InputStream in) throws IOException {
        return new String(in.readAllBytes(), StandardCharsets.UTF_8);
    }

    public static String readFile(Path path) throws IOException {
        return Files.readString(path, StandardCharsets.UTF_8);
    }
}
