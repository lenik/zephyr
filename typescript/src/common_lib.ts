/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import { createReadStream } from "node:fs";
import type { Readable, Writable } from "node:stream";

export function copyStream(input: Readable, output: Writable): Promise<void> {
  return new Promise((resolve, reject) => {
    input.on("error", reject);
    output.on("error", reject);
    input.on("end", resolve);
    input.pipe(output, { end: false });
  });
}

export async function copyFile(
  path: string,
  output: Writable,
): Promise<void> {
  const rs = createReadStream(path);
  await copyStream(rs, output);
}
