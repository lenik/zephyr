/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import { createReadStream } from "node:fs";

export function copyStream(input, output) {
  return new Promise((resolve, reject) => {
    input.on("error", reject);
    output.on("error", reject);
    input.on("end", resolve);
    input.pipe(output, { end: false });
  });
}

export async function copyFile(path, output) {
  const rs = createReadStream(path);
  await copyStream(rs, output);
}
