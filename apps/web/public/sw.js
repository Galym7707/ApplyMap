/* ApplyMap offline service worker.
 *
 * Three caches:
 *   - applymap-shell-v1: HTML / CSS / JS app shell (cache-first)
 *   - applymap-static-v1: images & fonts (cache-first, network fallback)
 *   - applymap-api-v1: read-only API responses for the reference catalog
 *     (stale-while-revalidate, capped TTL)
 *
 * Mutating API calls (POST/PUT/DELETE) are NEVER cached and always go to the
 * network. When offline, mutations fail and TanStack Query retries when
 * connectivity returns.
 *
 * The cache list and TTL are intentionally small — rural-school browsers may
 * have very little storage, so we keep less than ~5 MB of cached responses.
 */

const SHELL_CACHE = "applymap-shell-v1";
const STATIC_CACHE = "applymap-static-v1";
const API_CACHE = "applymap-api-v1";
const API_CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24h

const SHELL_ASSETS = [
  "/",
  "/offline.html",
  "/applymap-logo.png",
];

const CACHEABLE_API_PATHS = [
  "/api/universities",
  "/api/scholarships",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_ASSETS)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter((k) => ![SHELL_CACHE, STATIC_CACHE, API_CACHE].includes(k))
          .map((k) => caches.delete(k)),
      );
      await self.clients.claim();
    })(),
  );
});

function isCacheableApi(url) {
  return CACHEABLE_API_PATHS.some((path) => url.pathname.startsWith(path));
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(API_CACHE);
  const cached = await cache.match(request);
  const network = fetch(request)
    .then((response) => {
      if (response && response.status === 200) {
        const cloned = response.clone();
        const wrapped = new Response(cloned.body, {
          status: cloned.status,
          statusText: cloned.statusText,
          headers: new Headers(cloned.headers),
        });
        wrapped.headers.set("x-applymap-cached-at", Date.now().toString());
        cache.put(request, wrapped);
      }
      return response;
    })
    .catch(() => null);

  if (cached) {
    const cachedAt = Number(cached.headers.get("x-applymap-cached-at") || 0);
    if (Date.now() - cachedAt < API_CACHE_MAX_AGE_MS) {
      // serve cached and revalidate in background
      network.catch(() => null);
      return cached;
    }
  }

  const fresh = await network;
  return fresh || cached || new Response(
    JSON.stringify({ data: null, message: "offline" }),
    { status: 503, headers: { "content-type": "application/json" } },
  );
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) return;

  // API: stale-while-revalidate on whitelisted endpoints
  if (url.pathname.startsWith("/api/")) {
    if (isCacheableApi(url)) {
      event.respondWith(staleWhileRevalidate(request));
    }
    return;
  }

  // Navigation: serve cached shell, fall back to /offline.html
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(async () => {
        const cache = await caches.open(SHELL_CACHE);
        const offline = await cache.match("/offline.html");
        return offline || new Response("offline", { status: 503 });
      }),
    );
    return;
  }

  // Static assets: cache-first
  if (
    request.destination === "image" ||
    request.destination === "font" ||
    request.destination === "style" ||
    request.destination === "script"
  ) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(async (cache) => {
        const cached = await cache.match(request);
        if (cached) return cached;
        try {
          const response = await fetch(request);
          if (response.status === 200) cache.put(request, response.clone());
          return response;
        } catch {
          return cached || new Response("", { status: 504 });
        }
      }),
    );
  }
});
