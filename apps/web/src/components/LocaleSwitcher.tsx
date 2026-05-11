"use client";

import { Globe } from "lucide-react";
import { useState, useRef, useEffect } from "react";

import { cn } from "@/lib/utils";
import {
  LOCALES,
  LOCALE_LABELS,
  useTranslation,
  type Locale,
} from "@/i18n/I18nProvider";

/**
 * Compact 3-way locale switcher. Designed to live in the sidebar footer or
 * the header — toggleable dropdown to keep the chrome small on mobile.
 */
export function LocaleSwitcher() {
  const { locale, setLocale, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    function onClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    window.addEventListener("mousedown", onClickOutside);
    return () => window.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-label={t("common.language")}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm text-slate-500 transition-colors hover:bg-white hover:text-slate-700"
      >
        <Globe className="h-4 w-4" />
        <span className="flex-1 text-left">{LOCALE_LABELS[locale]}</span>
        <span className="text-xs uppercase text-slate-400">{locale}</span>
      </button>

      {open && (
        <ul
          role="listbox"
          className="absolute bottom-full left-0 mb-1 w-full overflow-hidden rounded-md border border-slate-200 bg-white shadow-lg"
        >
          {LOCALES.map((value) => {
            const active = value === locale;
            return (
              <li key={value}>
                <button
                  type="button"
                  role="option"
                  aria-selected={active}
                  onClick={() => {
                    setLocale(value as Locale);
                    setOpen(false);
                  }}
                  className={cn(
                    "flex w-full items-center justify-between px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-navy-50 font-medium text-navy-900"
                      : "text-slate-700 hover:bg-slate-50",
                  )}
                >
                  <span>{LOCALE_LABELS[value]}</span>
                  <span className="text-xs uppercase text-slate-400">
                    {value}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
