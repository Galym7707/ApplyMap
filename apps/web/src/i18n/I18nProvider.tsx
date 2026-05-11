/**
 * Lightweight i18n context for ApplyMap.
 *
 * No external dep — translations are static JSON imported at build time,
 * and the active locale is persisted to localStorage under
 * ``applymap.locale``. The browser's first-load default falls back to
 * ``navigator.language`` (en / ru / kk) and finally to ``en``.
 *
 * Keys are dotted paths into the message JSON (``"nav.advisor"`` ->
 * ``messages.nav.advisor``). Missing keys return the key itself so the UI
 * never crashes — but ``validate-messages.ts`` (run in CI) enforces that
 * all three locales export the same key set.
 */
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import enMessages from "./messages/en.json";
import ruMessages from "./messages/ru.json";
import kkMessages from "./messages/kk.json";

export const LOCALES = ["en", "ru", "kk"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";

const STORAGE_KEY = "applymap.locale";

const MESSAGES: Record<Locale, Record<string, unknown>> = {
  en: enMessages,
  ru: ruMessages,
  kk: kkMessages,
};

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "English",
  ru: "Русский",
  kk: "Қазақша",
};

function isLocale(value: string | null | undefined): value is Locale {
  return !!value && (LOCALES as readonly string[]).includes(value);
}

function detectInitialLocale(): Locale {
  if (typeof window === "undefined") return DEFAULT_LOCALE;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (isLocale(stored)) return stored;
  const browser = window.navigator.language?.slice(0, 2).toLowerCase();
  if (isLocale(browser)) return browser;
  return DEFAULT_LOCALE;
}

function resolveKey(
  messages: Record<string, unknown>,
  key: string,
): string | undefined {
  const parts = key.split(".");
  let cursor: unknown = messages;
  for (const part of parts) {
    if (cursor && typeof cursor === "object" && part in cursor) {
      cursor = (cursor as Record<string, unknown>)[part];
    } else {
      return undefined;
    }
  }
  return typeof cursor === "string" ? cursor : undefined;
}

function formatTemplate(
  template: string,
  vars?: Record<string, string | number>,
): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, name) =>
    name in vars ? String(vars[name]) : `{${name}}`,
  );
}

type I18nContextValue = {
  locale: Locale;
  setLocale: (next: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);

  // Hydrate on first client render.
  useEffect(() => {
    setLocaleState(detectInitialLocale());
  }, []);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, next);
      document.documentElement.lang = next;
    }
  }, []);

  // Keep <html lang> in sync.
  useEffect(() => {
    if (typeof document !== "undefined") document.documentElement.lang = locale;
  }, [locale]);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const primary = resolveKey(MESSAGES[locale], key);
      if (primary) return formatTemplate(primary, vars);
      const fallback = resolveKey(MESSAGES[DEFAULT_LOCALE], key);
      if (fallback) return formatTemplate(fallback, vars);
      return key;
    },
    [locale],
  );

  const value = useMemo<I18nContextValue>(
    () => ({ locale, setLocale, t }),
    [locale, setLocale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useTranslation(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    // Outside the provider (e.g. server components) — fall back to English
    // and a no-op setter so callers still get a typed shape.
    return {
      locale: DEFAULT_LOCALE,
      setLocale: () => undefined,
      t: (key, vars) => {
        const value = resolveKey(MESSAGES[DEFAULT_LOCALE], key);
        return value ? formatTemplate(value, vars) : key;
      },
    };
  }
  return ctx;
}

// Re-exported so tooling (validate-messages.ts) can introspect.
export const __messages = MESSAGES;
