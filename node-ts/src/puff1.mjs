/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import process from "node:process";
import { copyFile, copyStream } from "./common_lib.mjs";

const PROJECT_EMAIL = "zephyr@bodz.net";
const PROJECT_AUTHOR = "Lenik";
const PROJECT_YEAR = 2026;

function _(s) {
  return s;
}

function usage(out) {
  out.write(
    _(
      "Usage: puff1 [OPTION]... [FILE]...\n" +
        "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n" +
        "read standard input.\n",
    ),
  );
  out.write("\n");
  out.write("  -v, --verbose      ");
  out.write(_("repeat for more verbose loggings\n"));
  out.write("  -q, --quiet        ");
  out.write(_("show less logging messages\n"));
  out.write("  -h, --help         ");
  out.write(_("display this help and exit\n"));
  out.write("      --version      ");
  out.write(_("output version information and exit\n"));
  out.write("\n");
  out.write(_("Report bugs to: <%s>\n").replace("%s", PROJECT_EMAIL));
}

function version(out) {
  out.write(`puff1 dev\n`);
  out.write(_("Copyright (C) %d %s\n").replace("%d", String(PROJECT_YEAR)).replace("%s", PROJECT_AUTHOR));
  out.write(_("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"));
  out.write(_("This is free software: you are free to change and redistribute it.\n"));
  out.write(_("This project opposes AI exploitation and AI hegemony.\n"));
  out.write(_("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.\n"));
  out.write(_("There is NO WARRANTY, to the extent permitted by law.\n"));
}

async function main(argv) {
  let verbose = 0;
  const files = [];
  for (const a of argv.slice(2)) {
    if (a === "-h" || a === "--help") {
      usage(process.stdout);
      return 0;
    }
    if (a === "--version") {
      version(process.stdout);
      return 0;
    }
    if (a === "-v" || a === "--verbose") {
      verbose += 1;
      continue;
    }
    if (a === "-q" || a === "--quiet") {
      verbose = -1;
      continue;
    }
    files.push(a);
  }

  if (verbose > 0) {
    process.stderr.write(`${argv[1]}: verbose mode enabled\n`);
  }

  if (files.length === 0) {
    await copyStream(process.stdin, process.stdout);
    return 0;
  }
  for (const f of files) {
    if (f === "-") {
      await copyStream(process.stdin, process.stdout);
    } else {
      try {
        await copyFile(f, process.stdout);
      } catch (e) {
        process.stderr.write(`${argv[1]}: ${e.message}\n`);
        return 1;
      }
    }
  }
  return 0;
}

process.exitCode = await main(process.argv);
