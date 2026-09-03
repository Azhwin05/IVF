'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

/* ============================================================
   UI PREFERENCES
   ------------------------------------------------------------
   Per-user interface settings, owned by the browser rather than
   the server: they describe how one person likes to *see* the
   system, not clinical state, so they never need to sync across
   devices and must never block first paint.

   Every value is read after mount (not in the useState
   initializer) so the server and client render identically on
   the first pass and React doesn't throw a hydration mismatch.
   ============================================================ */

export type TextScale = 'standard' | 'large' | 'xl';
export type Density = 'comfortable' | 'compact';
export type SidebarSections = 'all-open' | 'active-only';
export type StartScreen = 'role-default' | string;

export interface Preferences {
  textScale: TextScale;
  density: Density;
  highContrast: boolean;
  reduceMotion: boolean;
  sidebarSections: SidebarSections;
  showClock: boolean;
  startScreen: StartScreen;
}

export const DEFAULT_PREFERENCES: Preferences = {
  textScale: 'standard',
  density: 'comfortable',
  highContrast: false,
  reduceMotion: false,
  sidebarSections: 'active-only',
  showClock: false,
  startScreen: 'role-default',
};

const STORAGE_KEY = 'ui-preferences';

interface PreferencesState {
  prefs: Preferences;
  setPref: <K extends keyof Preferences>(key: K, value: Preferences[K]) => void;
  reset: () => void;
  /** False until the stored values have been read, so the shell can
   *  avoid flashing default styling over a user's saved choices. */
  loaded: boolean;
}

const Ctx = createContext<PreferencesState | null>(null);

function readStored(): Partial<Preferences> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Partial<Preferences>;
    // Migrate the old standalone text-size key written by the previous
    // top-bar "Aa" control so nobody loses a setting they already made.
    const legacy = localStorage.getItem('text-scale');
    if (legacy === 'large' || legacy === 'xl') return { textScale: legacy };
  } catch {}
  return {};
}

export function PreferencesProvider({ children }: { children: React.ReactNode }) {
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFERENCES);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setPrefs({ ...DEFAULT_PREFERENCES, ...readStored() });
    setLoaded(true);
  }, []);

  const persist = useCallback((next: Preferences) => {
    setPrefs(next);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {}
  }, []);

  const setPref = useCallback(
    <K extends keyof Preferences>(key: K, value: Preferences[K]) => {
      setPrefs((cur) => {
        const next = { ...cur, [key]: value };
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch {}
        return next;
      });
    },
    []
  );

  const reset = useCallback(() => persist({ ...DEFAULT_PREFERENCES }), [persist]);

  return <Ctx.Provider value={{ prefs, setPref, reset, loaded }}>{children}</Ctx.Provider>;
}

export function usePreferences() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('usePreferences must be used inside PreferencesProvider');
  return ctx;
}

/** The root-level class list that turns preferences into actual styling.
 *  Kept here so the shell and the settings preview stay in sync. */
export function preferenceClasses(p: Preferences): string {
  return [
    p.textScale === 'large' && 'text-scale-large',
    p.textScale === 'xl' && 'text-scale-xl',
    p.density === 'compact' && 'density-compact',
    p.highContrast && 'high-contrast',
    p.reduceMotion && 'reduce-motion',
  ]
    .filter(Boolean)
    .join(' ');
}
