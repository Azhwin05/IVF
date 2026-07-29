'use client';

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import type { Role } from './data';
import type { ToastItem } from '@/components/ui/primitives';

export type ScreenId =
  | 'dashboard'
  | 'patients'
  | 'registration'
  | 'workspace'
  | 'appointments'
  | 'timeline'
  | 'monitoring'
  | 'plan'
  | 'embryology'
  | 'cryostorage'
  | 'transfer'
  | 'pregnancy'
  | 'laboratory'
  | 'pharmacy'
  | 'inventory'
  | 'billing'
  | 'accounting'
  | 'staff'
  | 'reports'
  | 'access'
  | 'audit'
  | 'administration';

interface AppState {
  role: Role | null;
  screen: ScreenId;
  history: ScreenId[];
  toasts: ToastItem[];
  paletteOpen: boolean;
  notifOpen: boolean;
  transferComplete: boolean;
  login: (role: Role) => void;
  logout: () => void;
  go: (screen: ScreenId) => void;
  back: () => void;
  toast: (t: Omit<ToastItem, 'id'>) => void;
  dismissToast: (id: number) => void;
  setPaletteOpen: (v: boolean) => void;
  setNotifOpen: (v: boolean) => void;
  completeTransfer: () => void;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<Role | null>(null);
  const [screen, setScreen] = useState<ScreenId>('dashboard');
  const [history, setHistory] = useState<ScreenId[]>([]);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [transferComplete, setTransferComplete] = useState(false);
  const toastId = useRef(0);

  const dismissToast = useCallback((id: number) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const toast = useCallback(
    (t: Omit<ToastItem, 'id'>) => {
      const id = ++toastId.current;
      setToasts((prev) => [...prev, { ...t, id }]);
      setTimeout(() => dismissToast(id), 4600);
    },
    [dismissToast]
  );

  const go = useCallback((next: ScreenId) => {
    setScreen((cur) => {
      if (cur !== next) setHistory((h) => [...h.slice(-12), cur]);
      return next;
    });
    setPaletteOpen(false);
    setNotifOpen(false);
  }, []);

  const back = useCallback(() => {
    setHistory((h) => {
      if (!h.length) return h;
      const prev = h[h.length - 1];
      setScreen(prev);
      return h.slice(0, -1);
    });
  }, []);

  const login = useCallback((r: Role) => {
    setRole(r);
    setScreen(r === 'management' ? 'reports' : r === 'embryologist' ? 'embryology' : r === 'receptionist' ? 'patients' : 'dashboard');
    setHistory([]);
  }, []);

  const logout = useCallback(() => {
    setRole(null);
    setHistory([]);
    setToasts([]);
    setTransferComplete(false);
  }, []);

  const completeTransfer = useCallback(() => setTransferComplete(true), []);

  return (
    <Ctx.Provider
      value={{
        role,
        screen,
        history,
        toasts,
        paletteOpen,
        notifOpen,
        transferComplete,
        login,
        logout,
        go,
        back,
        toast,
        dismissToast,
        setPaletteOpen,
        setNotifOpen,
        completeTransfer,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useApp() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useApp must be used inside AppProvider');
  return ctx;
}
