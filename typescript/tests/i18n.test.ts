import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { existsSync } from "node:fs";
import { join } from "node:path";

const mo = join("/build/po/zh_CN/LC_MESSAGES/zephyr.mo");

describe("i18n", () => {
  it("translates help strings when zh_CN catalog is available", async () => {
    if (!existsSync(mo)) {
      return;
    }
    process.env.ZEPHYR_LOCALEDIR = "/build/po";
    process.env.LANGUAGE = "zh_CN";
    process.env.LANG = "zh_CN.UTF-8";
    const { _, initI18n } = await import("../src/i18n.js");
    initI18n(import.meta.url);
    assert.equal(_("display this help and exit\n"), "显示此帮助并退出\n");
    assert.match(
      _(
        "Usage: some_puff1 [OPTION]... [FILE]...\n" +
          "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n" +
          "read standard input.\n",
      ),
      /^用法：/,
    );
  });
});
