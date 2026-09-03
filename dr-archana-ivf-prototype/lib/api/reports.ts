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

// ---- Discharge summary ----

export interface DischargeSummary {
  patient: { id: string; uhid: string; full_name: string; date_of_birth: string | null };
  couple: { id: string; partner_name: string } | null;
  cycles: { id: string; cycle_number: string; protocol: string; treatment: string; stage: string; started_at: string }[];
  consultations: { id: string; type: string; notes: string; date: string }[];
  investigations: { id: string; test_name: string; status: string; date: string }[];
  prescriptions: { id: string; category: string | null; line_count: number; date: string }[];
  monitoring_visits: { id: string; cycle_day: number; date: string; endometrium_mm: number; doctor_note: string | null }[];
  injections: { id: string; medicine_name: string; dose: string; status: string; administered_at: string | null }[];
  oocyte_assessments: { id: string; retrieval_date: string; oocytes_retrieved: number; mature_oocytes: number; normally_fertilised: number }[];
  embryos: { id: string; label: string; day: number; grade: string; status: string }[];
  embryo_transfers: { id: string; transfer_date: string; completed: boolean }[];
  current_storage: { id: string; address: string; embryo_id: string }[];
  pregnancy_outcomes: { id: string; outcome: string; transfer_date: string | null; estimated_due_date: string | null }[];
}

export function useDischargeSummary(patientId: string | null) {
  return useQuery({
    queryKey: ['discharge-summary', patientId],
    queryFn: () => apiFetch<DischargeSummary>(`/reports/discharge-summary/${patientId}`),
    enabled: !!patientId,
  });
}
