'use client';

import { AppQueryProvider } from '@/lib/query-client';
import { AuthProvider } from '@/lib/auth';
import { AppProvider } from '@/lib/store';
import { AppShell } from '@/components/layout/AppShell';

export default function Page() {
  return (
    <AppQueryProvider>
      <AuthProvider>
        <AppProvider>
          <AppShell />
        </AppProvider>
      </AuthProvider>
    </AppQueryProvider>
  );
}
