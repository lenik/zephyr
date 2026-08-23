/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import org.antlr.v4.runtime.CharStreams;
import org.antlr.v4.runtime.CommonTokenStream;

public final class Main {
    private static final String PROJECT_EMAIL = "zephyr@bodz.net";
    private static final int PROJECT_YEAR = 2026;
    private static final String PROJECT_AUTHOR = "Lenik";

    private Main() {}

    private static void usage(PrintStream out) {
        out.print(
            "Usage: some_puff1 [OPTION]... [FILE]...\n"
                + "Parse simple s-expressions and dump or format the AST.\n"
                + "With no FILE, or when FILE is -, read standard input.\n\n"
                + "  -d, --dump           AST dump\n"
                + "  -f, --format         format rewrite (default)\n"
                + "      --indent-size NUM  indentation width (default 4)\n"
                + "  -C, --color MODE     auto|always|never (default auto)\n"
                + "  -h, --help           display this help and exit\n"
                + "      --version        output version information and exit\n\n"
        );
        out.printf("Report bugs to: <%s>%n", PROJECT_EMAIL);
    }

    private static void version(PrintStream out) {
        String v = System.getProperty("zephyr.version", "dev");
        out.printf("some_puff1 %s%n", v);
        out.printf("Copyright (C) %d %s%n", PROJECT_YEAR, PROJECT_AUTHOR);
        out.print("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n");
        out.print("This is free software: you are free to change and redistribute it.\n");
        out.print("There is NO WARRANTY, to the extent permitted by law.\n");
    }

    private static int processInput(
        String text,
        boolean dump,
        commons.ColorMode color,
        int indentSize
    ) throws IOException {
        SomePuff1Lexer lexer = new SomePuff1Lexer(CharStreams.fromString(text));
        SomePuff1Parser parser = new SomePuff1Parser(new CommonTokenStream(lexer));
        SomePuff1Parser.ProgramContext tree = parser.program();
        if (parser.getNumberOfSyntaxErrors() > 0) {
            return 1;
        }
        commons.AstNode ast = commons.fromParseTree(tree.sexpr());
        StringBuilder sb = new StringBuilder();
        if (dump) {
            commons.astDump(ast, sb, color, 0);
        } else {
            commons.astFormat(ast, sb, color, indentSize, 0);
            sb.append('\n');
        }
        System.out.print(sb);
        return 0;
    }

    public static void main(String[] args) throws Exception {
        boolean dump = false;
        boolean format = false;
        int indentSize = 4;
        commons.ColorMode color = commons.ColorMode.AUTO;
        List<String> files = new ArrayList<>();

        for (int i = 0; i < args.length; i++) {
            String a = args[i];
            switch (a) {
                case "-h", "--help" -> {
                    usage(System.out);
                    return;
                }
                case "--version" -> {
                    version(System.out);
                    return;
                }
                case "-d", "--dump" -> dump = true;
                case "-f", "--format" -> format = true;
                case "-C", "--color" -> {
                    if (i + 1 >= args.length) {
                        System.err.println("some_puff1: missing color mode");
                        System.exit(1);
                    }
                    color = commons.parseColorMode(args[++i]);
                }
                case "--indent-size" -> {
                    if (i + 1 >= args.length) {
                        System.err.println("some_puff1: missing indent size");
                        System.exit(1);
                    }
                    indentSize = Integer.parseInt(args[++i]);
                }
                default -> files.add(a);
            }
        }

        if (!dump && !format) {
            dump = false;
        }

        int rc = 0;
        if (files.isEmpty()) {
            rc |= processInput(commons.readAll(System.in), dump, color, indentSize);
        } else {
            for (String file : files) {
                String text;
                if ("-".equals(file)) {
                    text = commons.readAll(System.in);
                } else {
                    text = commons.readFile(Path.of(file));
                }
                rc |= processInput(text, dump, color, indentSize);
            }
        }
        System.exit(rc);
    }
}
