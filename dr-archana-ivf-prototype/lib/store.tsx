'use client';

import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import type { Role, StaffUser } from './data';
import type { ToastItem } from '@/components/ui/primitives';
import { useAuth } from './auth';
import { toDisplayUser } from './roleMeta';

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
  | 'administration'
  | 'donors'
  | 'messaging';

interface AppState {
  role: Role | null;
  user: StaffUser | null;
  screen: ScreenId;
  history: ScreenId[];
  toasts: ToastItem[];
  paletteOpen: boolean;
  notifOpen: boolean;
  transferComplete: boolean;
  /** The patient every patient-scoped screen (Workspace, Timeline,
   * Monitoring, Plan, Transfer, Pregnancy, Embryology, Cryostorage) reads
   * from — set via `openPatient` from Patients/Registration/Dashboard,
   * replacing the old build's single hardcoded demo patient. */
  selectedPatientId: string | null;
  logout: () => void;
  go: (screen: ScreenId) => void;
  /** Sets the active patient and navigates to `screen` (defaults to the
   * patient workspace) in one call. */
  openPatient: (patientId: string, screen?: ScreenId) => void;
  back: () => void;
  toast: (t: Omit<ToastItem, 'id'>) => void;
  dismissToast: (id: number) => void;
  setPaletteOpen: (v: boolean) => void;
  setNotifOpen: (v: boolean) => void;
  completeTransfer: () => void;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const { user: authUser, logout: authLogout } = useAuth();
  const role = authUser ? toDisplayUser(authUser).role : null;
  const user = authUser ? toDisplayUser(authUser) : null;

  const [screen, setScreen] = useState<ScreenId>('dashboard');
  const [history, setHistory] = useState<ScreenId[]>([]);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [transferComplete, setTransferComplete] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const toastId = useRef(0);
  const prevAuthed = useRef(false);

  // Land on a role-appropriate starting screen the moment a login
  // succeeds (mirrors the old fake login()'s behavior), and reset
  // navigation/UI state the moment a session ends.
  useEffect(() => {
    if (authUser && !prevAuthed.current) {
      setScreen(role === 'management' ? 'reports' : role === 'embryologist' ? 'embryology' : role === 'receptionist' ? 'patients' : 'dashboard');
      setHistory([]);
    } else if (!authUser && prevAuthed.current) {
      setHistory([]);
      setToasts([]);
      setTransferComplete(false);
      setSelectedPatientId(null);
    }
    prevAuthed.current = !!authUser;
  }, [authUser, role]);

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

  const openPatient = useCallback(
    (patientId: string, screen: ScreenId = 'workspace') => {
      setSelectedPatientId(patientId);
      go(screen);
    },
    [go]
  );

  const back = useCallback(() => {
    setHistory((h) => {
      if (!h.length) return h;
      const prev = h[h.length - 1];
      setScreen(prev);
      return h.slice(0, -1);
    });
  }, []);

  const logout = useCallback(() => {
    authLogout();
  }, [authLogout]);

  const completeTransfer = useCallback(() => setTransferComplete(true), []);

  return (
    <Ctx.Provider
      value={{
        role,
        user,
        screen,
        history,
        toasts,
        paletteOpen,
        notifOpen,
        transferComplete,
        selectedPatientId,
        logout,
        go,
        openPatient,
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
