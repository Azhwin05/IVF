import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { CycleDistributionRow, DashboardMetrics } from './types';

export function useDashboardMetrics() {
  return useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => apiFetch<DashboardMetrics>('/reports/dashboard'),
    refetchInterval: 60_000,
  });
}

export function useCycleDistribution() {
  return useQuery({
    queryKey: ['cycle-distribution'],
    queryFn: () => apiFetch<CycleDistributionRow[]>('/reports/cycle-distribution'),
  });
}
