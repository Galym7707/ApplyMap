/**
 * Tiny IndexedDB wrapper for ApplyMap's offline cache.
 *
 * Stores the read-mostly data the app needs to work without a network:
 *   - profile        the current user's StudentProfile
 *   - achievements   list of the current user's achievements
 *   - universities   the full seeded catalog
 *   - scholarships   the seeded scholarship list
 *
 * No external dependency — we just use the browser's IndexedDB directly via
 * a Promise-wrapped helper. Records are namespaced by user id so multi-user
 * browsers don't leak data.
 */

const DB_NAME = "applymap-offline";
const DB_VERSION = 1;
const STORE = "kv";

type StoreKey =
  | `profile:${string}`
  | `achievements:${string}`
  | "universities"
  | "scholarships";

type Cached<T> = { value: T; storedAt: number };

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined" || !("indexedDB" in window)) {
      reject(new Error("IndexedDB not available"));
      return;
    }
    const req = window.indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error || new Error("IDB open failed"));
  });
}

async function put<T>(key: StoreKey, value: T): Promise<void> {
  try {
    const db = await openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put({ value, storedAt: Date.now() }, key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
    db.close();
  } catch {
    // best-effort cache; ignore quota / private-mode errors
  }
}

async function get<T>(key: StoreKey): Promise<Cached<T> | null> {
  try {
    const db = await openDb();
    const result = await new Promise<Cached<T> | null>((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).get(key);
      req.onsuccess = () => resolve((req.result as Cached<T>) || null);
      req.onerror = () => reject(req.error);
    });
    db.close();
    return result;
  } catch {
    return null;
  }
}

export const offlineCache = {
  async saveProfile(userId: string, profile: unknown) {
    await put(`profile:${userId}`, profile);
  },
  async loadProfile<T = unknown>(userId: string) {
    return get<T>(`profile:${userId}`);
  },
  async saveAchievements(userId: string, achievements: unknown) {
    await put(`achievements:${userId}`, achievements);
  },
  async loadAchievements<T = unknown>(userId: string) {
    return get<T>(`achievements:${userId}`);
  },
  async saveUniversities(universities: unknown) {
    await put("universities", universities);
  },
  async loadUniversities<T = unknown>() {
    return get<T>("universities");
  },
  async saveScholarships(scholarships: unknown) {
    await put("scholarships", scholarships);
  },
  async loadScholarships<T = unknown>() {
    return get<T>("scholarships");
  },
};

export type OfflineCached<T> = Cached<T>;
