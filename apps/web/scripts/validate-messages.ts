/**
 * Validates that every locale exports the same set of keys.
 *
 * Run with:  pnpm --filter @applymap/web exec tsx scripts/validate-messages.ts
 *
 * Exits non-zero if any locale has missing or extra keys vs the English
 * source-of-truth, so it can be wired into CI to prevent shipping a
 * half-translated UI.
 */
import enMessages from "../src/i18n/messages/en.json";
import ruMessages from "../src/i18n/messages/ru.json";
import kkMessages from "../src/i18n/messages/kk.json";

type Json = string | number | boolean | null | { [key: string]: Json } | Json[];

function flatten(obj: Json, prefix = ""): string[] {
  if (typeof obj !== "object" || obj === null || Array.isArray(obj)) {
    return [prefix];
  }
  return Object.entries(obj).flatMap(([k, v]) =>
    flatten(v as Json, prefix ? `${prefix}.${k}` : k),
  );
}

const en = new Set(flatten(enMessages as Json));
const locales: Array<[string, Set<string>]> = [
  ["ru", new Set(flatten(ruMessages as Json))],
  ["kk", new Set(flatten(kkMessages as Json))],
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
