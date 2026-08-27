import { apiFetch, tokenStore } from './client';
import type { TokenResponse, UserSummary } from './types';

export async function loginRequest(email: string, password: string, deviceLabel?: string): Promise<UserSummary> {
  const tokens = await apiFetch<TokenResponse>('/auth/login', {
    method: 'POST',
    body: { email, password, device_label: deviceLabel },
    skipAuthRetry: true,
  });
  tokenStore.set(tokens.access_token);
  try {
    return await apiFetch<UserSummary>('/auth/me');
  } catch (err) {
    tokenStore.set(null);
    throw err;
  }
}

export async function logoutRequest(): Promise<void> {
  try {
    await apiFetch<void>('/auth/logout', { method: 'POST', skipAuthRetry: true });
  } finally {
    tokenStore.set(null);
  }
}

export async function fetchCurrentUser(): Promise<UserSummary> {
  return apiFetch<UserSummary>('/auth/me');
}

/** Attempts to restore a session on page load using the httpOnly refresh
 * cookie (see backend/app/auth/router.py) — no request body needed, the
 * cookie travels automatically because apiFetch always sets
 * credentials: 'include'. Returns null (rather than throwing) on any
 * failure, since "not logged in yet" is an expected outcome here, not
 * an error worth surfacing. */
export async function trySilentLogin(): Promise<UserSummary | null> {
  try {
    const tokens = await apiFetch<TokenResponse>('/auth/refresh', { method: 'POST', skipAuthRetry: true });
    tokenStore.set(tokens.access_token);
    return await apiFetch<UserSummary>('/auth/me');
  } catch {
    tokenStore.set(null);
    return null;
  }
}
