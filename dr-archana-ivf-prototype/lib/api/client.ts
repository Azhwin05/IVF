/**
 * Thin fetch wrapper for the FastAPI backend. Two things make this more
 * than `fetch` with a base URL:
 *
 *  - Access token handling: the token lives in memory only (see
 *    tokenStore below), never localStorage — matching the backend's own
 *    security stance (see backend/app/auth/router.py's REFRESH_COOKIE
 *    comment). A page reload loses it, which is why AuthProvider always
 *    attempts a silent refresh on mount.
 *  - 401 handling: a request that fails with `token_expired` triggers
 *    exactly one refresh attempt (deduped across concurrent callers via
 *    `refreshInFlight`) and a single retry of the original request. If
 *    the refresh itself fails, every caller waiting on it gets logged
 *    out via `onAuthExpired`.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8600/api/v1';

export class ApiError extends Error {
  status: number;
  errorCode: string | null;
  requestId: string | null;

  constructor(status: number, message: string, errorCode: string | null, requestId: string | null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorCode = errorCode;
    this.requestId = requestId;
  }
}

type TokenListener = (token: string | null) => void;

/** Holds the access token in a module-level variable (memory only) and
 * lets AuthProvider subscribe so its React state stays in sync whenever
 * apiFetch silently rotates the token via a background refresh. */
export const tokenStore = (() => {
  let token: string | null = null;
  const listeners = new Set<TokenListener>();

  return {
    get: () => token,
    set(next: string | null) {
      token = next;
      listeners.forEach((l) => l(next));
    },
    subscribe(listener: TokenListener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
})();

/** Set by AuthProvider; called when a refresh attempt itself fails, so
 * the whole app can fall back to the Login screen in one place. */
let onAuthExpired: (() => void) | null = null;
export function setOnAuthExpired(handler: (() => void) | null) {
  onAuthExpired = handler;
}

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          credentials: 'include',
        });
        if (!res.ok) {
          tokenStore.set(null);
          onAuthExpired?.();
          return null;
        }
        const body = await res.json();
        tokenStore.set(body.access_token);
        return body.access_token as string;
      } catch {
        tokenStore.set(null);
        onAuthExpired?.();
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

export interface ApiFetchOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  /** Skip the auto-refresh-and-retry dance — used by the refresh/login calls themselves. */
  skipAuthRetry?: boolean;
}

export async function apiFetch<T = unknown>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, skipAuthRetry, headers, ...rest } = options;
  const token = tokenStore.get();

  const doFetch = async () => {
    const res = await fetch(`${API_BASE}${path}`, {
      ...rest,
      credentials: 'include',
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return res;
  };

  let res = await doFetch();

  if (res.status === 401 && !skipAuthRetry) {
    let errorCode: string | null = null;
    try {
      errorCode = (await res.clone().json())?.error_code ?? null;
    } catch {
      // non-JSON 401 body — fall through and still attempt a refresh
    }
    if (errorCode !== 'permission_denied') {
      const newToken = await refreshAccessToken();
      if (newToken) {
        res = await doFetch();
      }
    }
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const isJson = res.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? await res.json().catch(() => null) : null;

  if (!res.ok) {
    throw new ApiError(
      res.status,
      payload?.message ?? res.statusText ?? 'Request failed',
      payload?.error_code ?? null,
      payload?.request_id ?? null,
    );
  }

  return payload as T;
}
