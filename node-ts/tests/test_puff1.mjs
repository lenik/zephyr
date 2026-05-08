import { Readable, Writable } from "node:stream";
import assert from "node:assert/strict";
import { copyStream } from "../src/common_lib.mjs";

const input = Readable.from(Buffer.from("alpha\nbeta\n"));
let out = Buffer.alloc(0);
const output = new Writable({
  write(chunk, _enc, cb) {
    out = Buffer.concat([out, Buffer.from(chunk)]);
    cb();
  },
});

await copyStream(input, output);
assert.equal(out.toString("utf8"), "alpha\nbeta\n");
