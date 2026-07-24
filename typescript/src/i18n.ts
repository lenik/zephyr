/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import { readFileSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";
import Gettext from "node-gettext";
import { mo } from "gettext-parser";

export const TEXT_DOMAIN = "zephyr";

const gt = new Gettext({ sourceLocale: "en" });
gt.setTextDomain(TEXT_DOMAIN);

function localeCandidates(): string[] {
  const raw = [
    process.env.LANGUAGE,
    process.env.LC_ALL,
    process.env.LC_MESSAGES,
    process.env.LANG,
  ]
    .filter((v): v is string => !!v && v !== "C" && v !== "POSIX")
    .flatMap((v) => v.split(":"))
    .map((v) => v.trim())
    .filter(Boolean);

  const out: string[] = [];
  for (const loc of raw) {
    const noCharset = loc.split(".")[0] ?? loc;
    const noModifier = noCharset.split("@")[0] ?? noCharset;
    for (const c of [loc, noCharset, noModifier]) {
      if (c && !out.includes(c)) {
        out.push(c);
      }
    }
    const lang = noModifier.split("_")[0];
    if (lang && !out.includes(lang)) {
      out.push(lang);
    }
  }
  return out;
}

function resolveLocaleDirs(moduleUrl: string): string[] {
  const dirs: string[] = [];
  const envDir = process.env.ZEPHYR_LOCALEDIR;
  if (envDir) {
    dirs.push(envDir);
  }

  const here = dirname(fileURLToPath(moduleUrl));
  // Build tree: /build/puff1.js → /build/po
  dirs.push(join(here, "po"));
  // Installed: /usr/share/zephyr/puff1.js → /usr/share/locale
  dirs.push(resolve(here, "..", "locale"));
  // pnpm/npm dist: dist/src/puff1.js → <repo>/po
  dirs.push(resolve(here, "..", "..", "po"));
  dirs.push("/usr/share/locale");
  dirs.push("/usr/local/share/locale");

  return dirs;
}

function loadTranslations(moduleUrl: string): string | undefined {
  const locales = localeCandidates();
  if (locales.length === 0) {
    return undefined;
  }
  for (const localedir of resolveLocaleDirs(moduleUrl)) {
    for (const loc of locales) {
      const moPath = join(
        localedir,
        loc,
        "LC_MESSAGES",
        `${TEXT_DOMAIN}.mo`,
      );
      if (!existsSync(moPath)) {
        continue;
      }
      try {
        const parsed = mo.parse(readFileSync(moPath));
        gt.addTranslations(loc, TEXT_DOMAIN, parsed);
        gt.setLocale(loc);
        return loc;
      } catch {
        // try next candidate
      }
    }
  }
  return undefined;
}

/** Initialize gettext catalog for this process. Safe to call more than once. */
export function initI18n(moduleUrl: string = import.meta.url): void {
  loadTranslations(moduleUrl);
}

/** gettext `_` — returns msgstr when available, otherwise msgid. */
export function _(msgid: string): string {
  return gt.gettext(msgid);
}
