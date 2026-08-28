import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { UserSummary } from './types';

export function useDoctors() {
  return useQuery({
    queryKey: ['doctors'],
    queryFn: () => apiFetch<UserSummary[]>('/users/doctors'),
    staleTime: 5 * 60_000,
  });
}

export function useEmbryologists() {
  return useQuery({
    queryKey: ['embryologists'],
    queryFn: () => apiFetch<UserSummary[]>('/users/embryologists'),
    staleTime: 5 * 60_000,
  });
}
