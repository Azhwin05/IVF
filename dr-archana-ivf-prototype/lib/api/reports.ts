import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';
import type { CycleDistributionRow, DashboardMetrics, DoctorPerformanceRow, OutcomeRow, RevenueTrendRow } from './types';

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

export function useOutcomes(fromDate: string, toDate: string) {
  return useQuery({
    queryKey: ['outcomes', fromDate, toDate],
    queryFn: () => apiFetch<OutcomeRow[]>(`/reports/outcomes?from_date=${fromDate}&to_date=${toDate}`),
  });
}

export function useRevenueTrend(months = 6) {
  return useQuery({
    queryKey: ['revenue-trend', months],
    queryFn: () => apiFetch<RevenueTrendRow[]>(`/reports/revenue-trend?months=${months}`),
  });
}

export function useDoctorPerformance() {
  return useQuery({
    queryKey: ['doctor-performance'],
    queryFn: () => apiFetch<DoctorPerformanceRow[]>('/reports/doctor-performance'),
  });
}
