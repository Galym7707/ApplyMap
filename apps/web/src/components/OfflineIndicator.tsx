"use client";

import { useEffect, useState } from "react";

/**
 * Registers the offline service worker and renders a small status pill when
 * the user goes offline so they know the catalog they're seeing is cached.
 *
 * The pill is intentionally subtle (top-right, navy badge) — we don't want
 * to block UI when connectivity drops mid-session.
 */
export function OfflineIndicator() {
  const [online, setOnline] = useState(true);
  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setOnline(window.navigator.onLine);
    const onlineHandler = () => setOnline(true);
    const offlineHandler = () => setOnline(false);
    window.addEventListener("online", onlineHandler);
    window.addEventListener("offline", offlineHandler);
    return () => {
      window.removeEventListener("online", onlineHandler);
      window.removeEventListener("offline", offlineHandler);
    };
  }, []);

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !("serviceWorker" in navigator) ||
      process.env.NODE_ENV === "development"
    ) {
      return;
    }
    navigator.serviceWorker
      .register("/sw.js")
      .then(() => setRegistered(true))
      .catch(() => setRegistered(false));
  }, []);

  if (online) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed right-4 top-4 z-50 rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900 shadow-sm"
    >
      Offline — showing cached data
      {registered ? "" : " (cache unavailable)"}
    </div>
  );
}
