'use client';

import { AppProvider } from '@/lib/store';
import { AppShell } from '@/components/layout/AppShell';

export default function Page() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}
