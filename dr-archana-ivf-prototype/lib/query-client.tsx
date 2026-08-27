'use client';

import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiError } from './api/client';

function shouldRetry(failureCount: number, error: unknown): boolean {
  // 4xx errors (bad request, not found, permission denied, validation) are
  // never transient — retrying just repeats the same failure. Only retry
  // network hiccups / 5xx, and only twice.
  if (error instanceof ApiError && error.status < 500) return false;
  return failureCount < 2;
}

export function AppQueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: shouldRetry,
            staleTime: 30_000,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: false,
          },
        },
      })
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
