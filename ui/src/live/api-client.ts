// Tiny client for the engine API, with a patient retry for the free host that sleeps when idle.
export const BASE = (import.meta.env.VITE_ENGINE_URL as string | undefined) ?? 'http://127.0.0.1:8000';

export const WAKING_MESSAGE = 'Waking the free server, about 30 to 60 seconds. This page retries on its own.';
const RETRY_EVERY_MS = 5000;
const GIVE_UP_AFTER_MS = 90000;

export async function getJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(BASE + path, body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error((data as { error?: string }).error ?? res.statusText) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return data as T;
}

/** Retries every 5 s for up to 90 s when the server is asleep (network error or 502/503/504); real errors (400, 413...) throw at once. */
export async function getJsonRetry<T>(path: string, body?: unknown, onWaiting?: (waiting: boolean) => void): Promise<T> {
  const started = Date.now();
  for (;;) {
    try {
      const out = await getJson<T>(path, body);
      onWaiting?.(false);
      return out;
    } catch (e) {
      const status = (e as { status?: number }).status;
      const asleep = status === undefined || status === 502 || status === 503 || status === 504;
      if (!asleep || Date.now() - started > GIVE_UP_AFTER_MS) { onWaiting?.(false); throw e; }
      onWaiting?.(true);
      await new Promise((r) => setTimeout(r, RETRY_EVERY_MS));
    }
  }
}
