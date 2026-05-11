/**
 * Validates that every locale exports the same set of keys.
 *
 * Run with:  node scripts/validate-messages.mjs
 *
 * Exits non-zero if any locale has missing or extra keys vs the English
 * source-of-truth, so it can be wired into CI to prevent shipping a
 * half-translated UI.
 *
 * Plain ESM JavaScript — no build step required, runs everywhere Node
 * runs. This avoids dragging in tsx / ts-node just for one script.
 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const messagesDir = resolve(here, "..", "src", "i18n", "messages");

function load(locale) {
  const path = resolve(messagesDir, `${locale}.json`);
  return JSON.parse(readFileSync(path, "utf8"));
}

function flatten(obj, prefix = "") {
  if (typeof obj !== "object" || obj === null || Array.isArray(obj)) {
    return [prefix];
  }
  return Object.entries(obj).flatMap(([k, v]) =>
    flatten(v, prefix ? `${prefix}.${k}` : k),
  );
}

const en = new Set(flatten(load("en")));
const locales = [
  ["ru", new Set(flatten(load("ru")))],
  ["kk", new Set(flatten(load("kk")))],
];

let failures = 0;
for (const [name, keys] of locales) {
  const missing = [...en].filter((k) => !keys.has(k));
  const extra = [...keys].filter((k) => !en.has(k));
  if (missing.length === 0 && extra.length === 0) {
    console.log(`[i18n] ${name}: OK (${keys.size} keys)`);
    continue;
  }
  failures++;
  if (missing.length) {
    console.error(`[i18n] ${name}: missing ${missing.length} keys`);
    for (const k of missing) console.error(`  - ${k}`);
  }
  if (extra.length) {
    console.error(`[i18n] ${name}: extra ${extra.length} keys not in en`);
    for (const k of extra) console.error(`  + ${k}`);
  }
}

if (failures > 0) {
  console.error(`\n[i18n] FAILED for ${failures} locale(s)`);
  process.exit(1);
}
console.log("[i18n] All locales in sync");
